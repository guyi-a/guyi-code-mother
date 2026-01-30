-- 应用表 (PostgreSQL版本)

CREATE TABLE IF NOT EXISTS app
(
    id           BIGSERIAL PRIMARY KEY,
    appName      VARCHAR(256),
    cover        VARCHAR(512),
    initPrompt   TEXT,
    codeGenType  VARCHAR(64),
    deployKey    VARCHAR(64),
    deployedTime TIMESTAMP,
    priority     INTEGER DEFAULT 0 NOT NULL,
    userId       BIGINT NOT NULL,
    editTime     TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    createTime   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updateTime   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    isDelete     SMALLINT DEFAULT 0 NOT NULL,
    CONSTRAINT uk_deployKey UNIQUE (deployKey)
);

-- 添加注释
COMMENT ON TABLE app IS '应用表';
COMMENT ON COLUMN app.id IS 'id';
COMMENT ON COLUMN app.appName IS '应用名称';
COMMENT ON COLUMN app.cover IS '应用封面';
COMMENT ON COLUMN app.initPrompt IS '应用初始化的 prompt';
COMMENT ON COLUMN app.codeGenType IS '代码生成类型（枚举）';
COMMENT ON COLUMN app.deployKey IS '部署标识';
COMMENT ON COLUMN app.deployedTime IS '部署时间';
COMMENT ON COLUMN app.priority IS '优先级';
COMMENT ON COLUMN app.userId IS '创建用户id';
COMMENT ON COLUMN app.editTime IS '编辑时间';
COMMENT ON COLUMN app.createTime IS '创建时间';
COMMENT ON COLUMN app.updateTime IS '更新时间';
COMMENT ON COLUMN app.isDelete IS '是否删除';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_appName ON app (appName);
CREATE INDEX IF NOT EXISTS idx_userId ON app (userId);

-- 创建更新时间自动更新的触发器函数（如果不存在）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updateTime = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器，自动更新 updateTime
CREATE TRIGGER update_app_updated_at
    BEFORE UPDATE ON app
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

