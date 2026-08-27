"""
SSO com o CRM_MG — valida JWTs emitidos pelo backend do CRM para que o Dash RH,
agora embarcado como sistema nativo dentro do CRM, seja acessado sem login
próprio. Segue o mesmo padrão do ContAI (ContAI_PRO/app/infrastructure/auth/
crm_jwt.py): token HS256 assinado com o MESMO segredo do backend-fastapi do CRM
(env HR_CRM_JWT_SECRET, precisa ser idêntico ao JWT_SECRET de lá), carregando os
claims `sub` (id do usuário) e `email`.

Antes da migração o dashboard não tinha auth nenhuma e a Área Restrita usava só
um header de senha compartilhada em texto puro. Agora:
  - todos os endpoints /api/* exigem `Authorization: Bearer <jwt-do-crm>` válido;
  - a Área Restrita (/api/confidential/*) exige, além do JWT, que o e-mail esteja
    na allowlist HR_CONFIDENTIAL_ALLOWLIST (lista separada por vírgula). Se a
    allowlist estiver vazia, o acesso à Área Restrita fica liberado para
    qualquer usuário já autenticado pelo CRM (fail-open consciente — a barreira
    principal, o SSO, continua de pé).
"""

import logging

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)


def _extract_bearer(authorization: str | None) -> str | None:
    """Extrai o token cru de um header 'Authorization: Bearer <token>'."""
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def _email_domain_allowed(email: str) -> bool:
    domains = [d.strip().lower() for d in settings.allowed_email_domains.split(",") if d.strip()]
    if not domains:
        return True
    return "@" in email and email.rsplit("@", 1)[1].lower() in domains


def get_crm_user(authorization: str | None = Header(None)) -> dict:
    """
    Dependency: valida o Bearer JWT do CRM e devolve um dict com os dados do
    usuário. Lança 401 se o token estiver ausente/inválido/expirado ou se o
    domínio do e-mail não for autorizado.
    """
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso ausente.",
        )

    secret = (settings.crm_jwt_secret or "").strip()
    if not secret:
        logger.error("[CRM JWT] HR_CRM_JWT_SECRET não configurado; recusando todos os tokens.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SSO com o CRM não configurado no servidor.",
        )

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada."
        )
    except jwt.InvalidTokenError as exc:
        logger.info("[CRM JWT] Token inválido: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de acesso inválido."
        )

    email = (payload.get("email") or "").strip().lower()
    if not _email_domain_allowed(email):
        logger.warning("[CRM JWT] Domínio não autorizado: %s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Domínio de e-mail não autorizado."
        )

    return {
        "id": payload.get("sub", ""),
        "email": email,
        "name": payload.get("name", email.split("@")[0] if email else ""),
    }


def require_confidential_access(user: dict = Depends(get_crm_user)) -> dict:
    """
    Dependency da Área Restrita: exige JWT válido + e-mail na allowlist
    HR_CONFIDENTIAL_ALLOWLIST. Allowlist vazia => libera para qualquer usuário
    autenticado pelo CRM.
    """
    allowlist = [e.strip().lower() for e in settings.confidential_allowlist.split(",") if e.strip()]
    if allowlist and user["email"] not in allowlist:
        logger.warning("[CRM JWT] Acesso à Área Restrita negado para: %s", user["email"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso negado: usuário sem permissão para o detalhamento nominal.",
        )
    return user
