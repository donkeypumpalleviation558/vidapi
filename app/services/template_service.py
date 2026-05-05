from __future__ import annotations

import json

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import template_crud
from app.db.template_models import Template, TemplateVersion
from app.models.composition import Composition

logger = structlog.get_logger(__name__)


class TemplateNotFoundError(Exception):
    """Raised when a template is not found."""

    def __init__(self, template_id: str) -> None:
        self.template_id = template_id
        super().__init__(f"Template {template_id} not found")


class TemplateDeletedError(Exception):
    """Raised when attempting to modify a soft-deleted template."""

    def __init__(self, template_id: str) -> None:
        self.template_id = template_id
        super().__init__(f"Template {template_id} is deleted")


class TemplateAlreadyDeletedError(Exception):
    """Raised when attempting to delete an already-deleted template."""

    def __init__(self, template_id: str) -> None:
        self.template_id = template_id
        super().__init__(f"Template {template_id} is already deleted")


class TemplateService:
    async def create_template(
        self,
        session: AsyncSession,
        *,
        name: str,
        composition: Composition,
        description: str | None = None,
        variable_schema: dict | None = None,
    ) -> tuple[Template, TemplateVersion]:
        composition_json = composition.model_dump_json()
        variable_schema_json = (
            json.dumps(variable_schema) if variable_schema is not None else None
        )

        template, version = await template_crud.create_template(
            session,
            name=name,
            composition_json=composition_json,
            description=description,
            variable_schema_json=variable_schema_json,
        )

        await logger.ainfo(
            "template_created",
            template_id=template.id,
            version_id=version.id,
            name=name,
        )
        return template, version

    async def get_template(
        self,
        session: AsyncSession,
        template_id: str,
    ) -> tuple[Template, TemplateVersion | None]:
        template = await template_crud.get_template_by_id(session, template_id)
        if template is None:
            raise TemplateNotFoundError(template_id)

        active_version = await template_crud.get_active_version(session, template)
        return template, active_version

    async def list_templates(
        self,
        session: AsyncSession,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[tuple[Template, int]], int]:
        """Return paginated templates with version counts.

        Returns (list_of_(template, version_count), total).
        """
        templates, total = await template_crud.list_templates(
            session, offset=offset, limit=limit
        )

        result: list[tuple[Template, int]] = []
        for tmpl in templates:
            count = await template_crud.get_version_count(session, tmpl.id)
            result.append((tmpl, count))

        return result, total

    async def update_template(
        self,
        session: AsyncSession,
        template_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        composition: Composition | None = None,
        variable_schema: dict | None = None,
    ) -> tuple[Template, TemplateVersion | None]:
        template = await template_crud.get_template_by_id(session, template_id)
        if template is None:
            raise TemplateNotFoundError(template_id)
        if template.is_deleted:
            raise TemplateDeletedError(template_id)

        composition_json = (
            composition.model_dump_json() if composition is not None else None
        )
        variable_schema_json = (
            json.dumps(variable_schema) if variable_schema is not None else None
        )

        template, new_version = await template_crud.update_template(
            session,
            template_id,
            name=name,
            description=description,
            composition_json=composition_json,
            variable_schema_json=variable_schema_json,
        )

        await logger.ainfo(
            "template_updated",
            template_id=template.id,
            new_version_id=new_version.id if new_version else None,
        )
        return template, new_version

    async def delete_template(
        self,
        session: AsyncSession,
        template_id: str,
    ) -> Template:
        template = await template_crud.get_template_by_id(session, template_id)
        if template is None:
            raise TemplateNotFoundError(template_id)
        if template.is_deleted:
            raise TemplateAlreadyDeletedError(template_id)

        template = await template_crud.soft_delete_template(session, template_id)

        await logger.ainfo("template_deleted", template_id=template.id)
        return template
