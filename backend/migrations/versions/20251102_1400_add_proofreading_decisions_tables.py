"""Add proofreading decisions and feedback tables

Revision ID: add_proofreading_decisions
Revises: 20251031_1830_add_metadata_to_worklist_items
Create Date: 2025-11-02 14:00:00.000000

Task: T7.1 [US2][P0] Proofreading 决策与反馈调优批次迁移
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_proofreading_decisions'
down_revision = '20251031_1830'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建校对决策相关表"""

    # 1. 创建 proofreading_history 表
    op.create_table(
        'proofreading_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),

        # 执行信息
        sa.Column('executed_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('execution_duration_ms', sa.Integer(), nullable=True),
        sa.Column('engine_version', sa.String(20), nullable=True),

        # 问题统计
        sa.Column('total_issues_found', sa.Integer(), server_default='0', nullable=False),
        sa.Column('critical_issues_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('warning_issues_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('info_issues_count', sa.Integer(), server_default='0', nullable=False),

        # 决策统计
        sa.Column('accepted_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('rejected_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('modified_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('pending_count', sa.Integer(), server_default='0', nullable=False),

        # 反馈统计
        sa.Column('feedback_provided_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('pending_feedback_count', sa.Integer(), server_default='0', nullable=False),

        # 分引擎统计
        sa.Column('deterministic_issues_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('ai_issues_count', sa.Integer(), server_default='0', nullable=False),

        # 结果快照
        sa.Column('issues_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('config_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # 审计字段
        sa.Column('executed_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),

        comment='校对执行历史记录表，存储每次校对的执行结果和统计信息'
    )

    # 为 proofreading_history 创建索引
    op.create_index(
        'idx_proofreading_history_article_id',
        'proofreading_history',
        ['article_id']
    )

    op.create_index(
        'idx_proofreading_history_executed_at',
        'proofreading_history',
        ['executed_at'],
        postgresql_using='btree',
        postgresql_ops={'executed_at': 'DESC'}
    )

    # 部分索引：只索引有待处理反馈的记录
    op.create_index(
        'idx_proofreading_history_pending_feedback',
        'proofreading_history',
        ['article_id'],
        postgresql_where=sa.text('pending_feedback_count > 0')
    )

    # 2. 创建 proofreading_decisions 表
    op.create_table(
        'proofreading_decisions',
        sa.Column('id', sa.Integer(), nullable=False),

        # 关联信息
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('suggestion_id', sa.String(100), nullable=False),
        sa.Column('proofreading_history_id', sa.Integer(), nullable=True),

        # 决策核心数据
        sa.Column('decision_type', sa.String(20), nullable=False),
        sa.Column('decision_rationale', sa.Text(), nullable=True),
        sa.Column('modified_content', sa.Text(), nullable=True),

        # 原始建议信息（快照）
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('suggested_text', sa.Text(), nullable=False),
        sa.Column('rule_id', sa.String(20), nullable=False),
        sa.Column('rule_category', sa.String(10), nullable=True),
        sa.Column('issue_position', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # 反馈数据
        sa.Column('feedback_provided', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('feedback_category', sa.String(50), nullable=True),
        sa.Column('feedback_notes', sa.Text(), nullable=True),
        sa.Column('feedback_status', sa.String(20), server_default='pending', nullable=False),

        # 审计字段
        sa.Column('decided_by', sa.Integer(), nullable=False),
        sa.Column('decided_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['proofreading_history_id'], ['proofreading_history.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('article_id', 'suggestion_id', name='uq_article_suggestion'),

        comment='校对决策记录表，存储用户对校对建议的接受、拒绝或修改决策'
    )

    # 为 proofreading_decisions 创建索引
    op.create_index(
        'idx_proofreading_decisions_article_id',
        'proofreading_decisions',
        ['article_id']
    )

    op.create_index(
        'idx_proofreading_decisions_rule_id',
        'proofreading_decisions',
        ['rule_id']
    )

    op.create_index(
        'idx_proofreading_decisions_feedback_status',
        'proofreading_decisions',
        ['feedback_status'],
        postgresql_where=sa.text('feedback_provided = true')
    )

    op.create_index(
        'idx_proofreading_decisions_decided_at',
        'proofreading_decisions',
        ['decided_at']
    )

    op.create_index(
        'idx_proofreading_decisions_decision_type',
        'proofreading_decisions',
        ['decision_type']
    )

    # 复合索引用于统计查询
    op.create_index(
        'idx_proofreading_decisions_stats',
        'proofreading_decisions',
        ['rule_category', 'decision_type', 'decided_at']
    )

    # 3. 创建 feedback_tuning_jobs 表
    op.create_table(
        'feedback_tuning_jobs',
        sa.Column('id', sa.Integer(), nullable=False),

        # 任务定义
        sa.Column('job_type', sa.String(30), nullable=False),
        sa.Column('job_name', sa.String(200), nullable=True),
        sa.Column('job_description', sa.Text(), nullable=True),

        # 处理范围
        sa.Column('target_rule_ids', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('target_categories', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),

        # 处理统计
        sa.Column('total_decisions_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('processed_count', sa.Integer(), server_default='0', nullable=False),

        # 任务状态
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('progress_percent', sa.Integer(), server_default='0', nullable=False),

        # 执行结果
        sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # 时间戳
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),

        sa.PrimaryKeyConstraint('id'),

        # 约束
        sa.CheckConstraint('progress_percent >= 0 AND progress_percent <= 100', name='chk_progress_percent'),
        sa.CheckConstraint('end_date >= start_date', name='chk_date_range'),

        comment='反馈调优任务表，用于批量分析用户反馈并生成规则优化建议'
    )

    # 为 feedback_tuning_jobs 创建索引
    op.create_index(
        'idx_feedback_tuning_jobs_status',
        'feedback_tuning_jobs',
        ['status']
    )

    op.create_index(
        'idx_feedback_tuning_jobs_created_at',
        'feedback_tuning_jobs',
        ['created_at'],
        postgresql_using='btree',
        postgresql_ops={'created_at': 'DESC'}
    )

    op.create_index(
        'idx_feedback_tuning_jobs_type_status',
        'feedback_tuning_jobs',
        ['job_type', 'status']
    )

    # 4. 添加触发器更新 updated_at 字段
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    op.execute("""
        CREATE TRIGGER update_proofreading_decisions_updated_at
        BEFORE UPDATE ON proofreading_decisions
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    # 5. 创建枚举类型（如果需要）
    # 注意：在实际使用中，可能需要先检查枚举类型是否存在
    decision_type_enum = postgresql.ENUM(
        'accepted', 'rejected', 'modified',
        name='decision_type_enum',
        create_type=False
    )
    decision_type_enum.create(op.get_bind(), checkfirst=True)

    feedback_status_enum = postgresql.ENUM(
        'pending', 'in_progress', 'completed', 'failed',
        name='feedback_status_enum',
        create_type=False
    )
    feedback_status_enum.create(op.get_bind(), checkfirst=True)

    job_type_enum = postgresql.ENUM(
        'rule_tuning', 'prompt_optimization', 'batch_analysis',
        name='job_type_enum',
        create_type=False
    )
    job_type_enum.create(op.get_bind(), checkfirst=True)

    tuning_job_status_enum = postgresql.ENUM(
        'pending', 'running', 'completed', 'failed',
        name='tuning_job_status_enum',
        create_type=False
    )
    tuning_job_status_enum.create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """删除校对决策相关表"""

    # 1. 删除触发器
    op.execute('DROP TRIGGER IF EXISTS update_proofreading_decisions_updated_at ON proofreading_decisions')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column')

    # 2. 删除 feedback_tuning_jobs 表的索引
    op.drop_index('idx_feedback_tuning_jobs_type_status', table_name='feedback_tuning_jobs')
    op.drop_index('idx_feedback_tuning_jobs_created_at', table_name='feedback_tuning_jobs')
    op.drop_index('idx_feedback_tuning_jobs_status', table_name='feedback_tuning_jobs')

    # 3. 删除 feedback_tuning_jobs 表
    op.drop_table('feedback_tuning_jobs')

    # 4. 删除 proofreading_decisions 表的索引
    op.drop_index('idx_proofreading_decisions_stats', table_name='proofreading_decisions')
    op.drop_index('idx_proofreading_decisions_decision_type', table_name='proofreading_decisions')
    op.drop_index('idx_proofreading_decisions_decided_at', table_name='proofreading_decisions')
    op.drop_index('idx_proofreading_decisions_feedback_status', table_name='proofreading_decisions')
    op.drop_index('idx_proofreading_decisions_rule_id', table_name='proofreading_decisions')
    op.drop_index('idx_proofreading_decisions_article_id', table_name='proofreading_decisions')

    # 5. 删除 proofreading_decisions 表
    op.drop_table('proofreading_decisions')

    # 6. 删除 proofreading_history 表的索引
    op.drop_index('idx_proofreading_history_pending_feedback', table_name='proofreading_history')
    op.drop_index('idx_proofreading_history_executed_at', table_name='proofreading_history')
    op.drop_index('idx_proofreading_history_article_id', table_name='proofreading_history')

    # 7. 删除 proofreading_history 表
    op.drop_table('proofreading_history')

    # 8. 删除枚举类型（谨慎操作，因为可能其他表也在使用）
    # 注意：在生产环境中，删除枚举类型需要特别小心
    # op.execute('DROP TYPE IF EXISTS decision_type_enum CASCADE')
    # op.execute('DROP TYPE IF EXISTS feedback_status_enum CASCADE')
    # op.execute('DROP TYPE IF EXISTS job_type_enum CASCADE')
    # op.execute('DROP TYPE IF EXISTS tuning_job_status_enum CASCADE')
