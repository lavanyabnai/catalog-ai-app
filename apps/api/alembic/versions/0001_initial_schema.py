"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2026-05-04

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE user_role AS ENUM ('admin', 'member');
        CREATE TYPE product_status AS ENUM ('draft', 'processing', 'ready_for_review', 'approved', 'archived');
        CREATE TYPE attribute_value_type AS ENUM ('string', 'enum', 'number', 'boolean', 'multi_enum');
        CREATE TYPE job_type AS ENUM ('image', 'video');
        CREATE TYPE job_status AS ENUM ('queued', 'running', 'succeeded', 'failed');
        CREATE TYPE asset_kind AS ENUM ('image_on_model', 'video_on_model', 'image_variant');
        CREATE TYPE bundle_status AS ENUM ('pending', 'approved');

        CREATE TABLE tenants (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            clerk_user_id VARCHAR(255),
            email VARCHAR(255) NOT NULL,
            role user_role NOT NULL DEFAULT 'member',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_users_tenant_id ON users(tenant_id);

        CREATE TABLE brand_kits (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            name VARCHAR(255) NOT NULL,
            color_palette JSONB,
            tone_notes TEXT,
            allowed_scenes JSONB,
            allowed_personas JSONB,
            required_aspect_ratios JSONB NOT NULL DEFAULT '["4:5","1:1","9:16"]',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_brand_kits_tenant_id ON brand_kits(tenant_id);

        CREATE TABLE categories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID,
            parent_id UUID REFERENCES categories(id),
            slug VARCHAR(255) NOT NULL,
            display_name VARCHAR(255) NOT NULL,
            path VARCHAR(1000) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_categories_tenant_id ON categories(tenant_id);
        CREATE INDEX ix_categories_parent_id ON categories(parent_id);

        CREATE TABLE attribute_definitions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            category_id UUID NOT NULL REFERENCES categories(id),
            key VARCHAR(100) NOT NULL,
            display_name VARCHAR(255) NOT NULL,
            value_type attribute_value_type NOT NULL,
            is_required BOOLEAN NOT NULL DEFAULT false,
            allowed_values JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_attribute_definitions_category_id ON attribute_definitions(category_id);

        CREATE TABLE model_personas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID,
            display_name VARCHAR(255) NOT NULL,
            body_type VARCHAR(100) NOT NULL,
            ethnicity VARCHAR(100) NOT NULL,
            age_range VARCHAR(50) NOT NULL,
            height_cm INTEGER NOT NULL,
            gender_presentation VARCHAR(50) NOT NULL,
            hair VARCHAR(255) NOT NULL,
            system_managed BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_model_personas_tenant_id ON model_personas(tenant_id);

        CREATE TABLE products (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            code VARCHAR(100) NOT NULL,
            name VARCHAR(500) NOT NULL,
            category_id UUID REFERENCES categories(id),
            brand_kit_id UUID REFERENCES brand_kits(id),
            source_image_key VARCHAR(1000),
            status product_status NOT NULL DEFAULT 'draft',
            attributes JSONB NOT NULL DEFAULT '{}',
            gtin VARCHAR(50),
            mpn VARCHAR(100),
            brand VARCHAR(255),
            slug VARCHAR(500),
            meta_title VARCHAR(500),
            meta_description TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_products_tenant_id ON products(tenant_id);
        CREATE UNIQUE INDEX uq_products_tenant_code_active ON products(tenant_id, code) WHERE status != 'archived';

        CREATE TABLE variants (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            product_id UUID NOT NULL REFERENCES products(id),
            sku_code VARCHAR(100) NOT NULL,
            color VARCHAR(100),
            size VARCHAR(50),
            attributes JSONB NOT NULL DEFAULT '{}',
            gtin VARCHAR(50),
            mpn VARCHAR(100),
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_variants_tenant_id ON variants(tenant_id);
        CREATE INDEX ix_variants_product_id ON variants(product_id);
        CREATE UNIQUE INDEX uq_variants_tenant_sku_active ON variants(tenant_id, sku_code) WHERE deleted_at IS NULL;

        CREATE TABLE generation_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            product_id UUID NOT NULL REFERENCES products(id),
            type job_type NOT NULL,
            status job_status NOT NULL DEFAULT 'queued',
            provider VARCHAR(100) NOT NULL DEFAULT 'fal',
            model_id VARCHAR(255) NOT NULL DEFAULT '',
            prompt JSONB NOT NULL DEFAULT '{}',
            params JSONB NOT NULL DEFAULT '{}',
            cost_cents INTEGER,
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            error TEXT,
            error_code VARCHAR(100),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_generation_jobs_tenant_id ON generation_jobs(tenant_id);
        CREATE INDEX ix_generation_jobs_product_id ON generation_jobs(product_id);
        CREATE INDEX ix_generation_jobs_product_created ON generation_jobs(product_id, created_at);

        CREATE TABLE generated_assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            product_id UUID NOT NULL REFERENCES products(id),
            job_id UUID NOT NULL REFERENCES generation_jobs(id),
            kind asset_kind NOT NULL,
            storage_key VARCHAR(1000) NOT NULL,
            width INTEGER,
            height INTEGER,
            duration_ms INTEGER,
            mime_type VARCHAR(100) NOT NULL DEFAULT 'image/webp',
            metadata JSONB NOT NULL DEFAULT '{}',
            version INTEGER NOT NULL DEFAULT 1,
            is_hero BOOLEAN NOT NULL DEFAULT false,
            parent_asset_id UUID REFERENCES generated_assets(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_generated_assets_tenant_id ON generated_assets(tenant_id);
        CREATE INDEX ix_generated_assets_product_id ON generated_assets(product_id);
        CREATE INDEX ix_generated_assets_job_id ON generated_assets(job_id);

        CREATE TABLE asset_bundles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            product_id UUID NOT NULL REFERENCES products(id),
            version INTEGER NOT NULL DEFAULT 1,
            status bundle_status NOT NULL DEFAULT 'pending',
            approved_by UUID REFERENCES users(id),
            approved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_asset_bundles_tenant_id ON asset_bundles(tenant_id);
        CREATE INDEX ix_asset_bundles_product_id ON asset_bundles(product_id);

        CREATE TABLE audit_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
            entity_type VARCHAR(100) NOT NULL,
            entity_id UUID NOT NULL,
            action VARCHAR(100) NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_audit_events_tenant_id ON audit_events(tenant_id);
        CREATE INDEX ix_audit_events_entity ON audit_events(entity_type, entity_id);

        CREATE OR REPLACE FUNCTION _updated_at_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW() AT TIME ZONE 'UTC';
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_products_updated_at
            BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION _updated_at_trigger();
        CREATE TRIGGER trg_variants_updated_at
            BEFORE UPDATE ON variants FOR EACH ROW EXECUTE FUNCTION _updated_at_trigger();

        ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
        ALTER TABLE brand_kits ENABLE ROW LEVEL SECURITY;
        ALTER TABLE products ENABLE ROW LEVEL SECURITY;
        ALTER TABLE variants ENABLE ROW LEVEL SECURITY;
        ALTER TABLE generation_jobs ENABLE ROW LEVEL SECURITY;
        ALTER TABLE generated_assets ENABLE ROW LEVEL SECURITY;
        ALTER TABLE asset_bundles ENABLE ROW LEVEL SECURITY;
        ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
        ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
        ALTER TABLE attribute_definitions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE model_personas ENABLE ROW LEVEL SECURITY;

        CREATE POLICY tenant_isolation ON tenants
            USING (id = current_setting('app.current_tenant_id', true)::uuid);
        CREATE POLICY tenant_isolation ON users
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        CREATE POLICY tenant_isolation ON brand_kits
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        CREATE POLICY tenant_isolation ON products
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        CREATE POLICY tenant_isolation ON variants
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        CREATE POLICY tenant_isolation ON generation_jobs
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        CREATE POLICY tenant_isolation ON generated_assets
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        CREATE POLICY tenant_isolation ON asset_bundles
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        CREATE POLICY tenant_isolation ON audit_events
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        CREATE POLICY tenant_isolation ON categories
            USING (tenant_id IS NULL OR tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        CREATE POLICY tenant_isolation ON attribute_definitions
            USING (tenant_id IS NULL OR tenant_id = current_setting('app.current_tenant_id', true)::uuid);
        CREATE POLICY tenant_isolation ON model_personas
            USING (tenant_id IS NULL OR tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TRIGGER IF EXISTS trg_products_updated_at ON products;
        DROP TRIGGER IF EXISTS trg_variants_updated_at ON variants;
        DROP FUNCTION IF EXISTS _updated_at_trigger();
        DROP TABLE IF EXISTS audit_events CASCADE;
        DROP TABLE IF EXISTS asset_bundles CASCADE;
        DROP TABLE IF EXISTS generated_assets CASCADE;
        DROP TABLE IF EXISTS generation_jobs CASCADE;
        DROP TABLE IF EXISTS variants CASCADE;
        DROP TABLE IF EXISTS products CASCADE;
        DROP TABLE IF EXISTS model_personas CASCADE;
        DROP TABLE IF EXISTS attribute_definitions CASCADE;
        DROP TABLE IF EXISTS categories CASCADE;
        DROP TABLE IF EXISTS brand_kits CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        DROP TABLE IF EXISTS tenants CASCADE;
        DROP TYPE IF EXISTS bundle_status;
        DROP TYPE IF EXISTS asset_kind;
        DROP TYPE IF EXISTS job_status;
        DROP TYPE IF EXISTS job_type;
        DROP TYPE IF EXISTS attribute_value_type;
        DROP TYPE IF EXISTS product_status;
        DROP TYPE IF EXISTS user_role;
    """)
