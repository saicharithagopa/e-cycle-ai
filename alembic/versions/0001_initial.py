"""Initial schema: device classes, profiles, scoring rules, assessments.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "device_classes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(64), unique=True, nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("supported", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_device_classes_name", "device_classes", ["name"])

    op.create_table(
        "device_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_class_id", sa.Integer(), sa.ForeignKey("device_classes.id"), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("components_json", sa.Text(), nullable=False),
        sa.Column("materials_json", sa.Text(), nullable=False),
        sa.Column("hazards_json", sa.Text(), nullable=False),
        sa.Column("caveats", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_device_profiles_device_class_id", "device_profiles", ["device_class_id"])

    op.create_table(
        "scoring_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("factor", sa.String(64), unique=True, nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_scoring_rules_factor", "scoring_rules", ["factor"])

    op.create_table(
        "assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_class", sa.String(64), nullable=False),
        sa.Column("age_years", sa.Integer(), nullable=False),
        sa.Column("powers_on", sa.Boolean(), nullable=False),
        sa.Column("condition", sa.String(64), nullable=False),
        sa.Column("image_deleted", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_assessments_device_class", "assessments", ["device_class"])

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id"), unique=True, nullable=False),
        sa.Column("device_class", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
    )
    op.create_index("ix_predictions_assessment_id", "predictions", ["assessment_id"])

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id"), unique=True, nullable=False),
        sa.Column("pathway", sa.String(32), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("factors_json", sa.Text(), nullable=False),
        sa.Column("explanation_version", sa.String(64), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
    )
    op.create_index("ix_recommendations_assessment_id", "recommendations", ["assessment_id"])


def downgrade() -> None:
    op.drop_table("recommendations")
    op.drop_table("predictions")
    op.drop_table("assessments")
    op.drop_table("scoring_rules")
    op.drop_table("device_profiles")
    op.drop_table("device_classes")
