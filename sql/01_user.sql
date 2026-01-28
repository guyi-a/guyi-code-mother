-- 用户表

CREATE TABLE IF NOT EXISTS "user"
(
    id           BIGSERIAL PRIMARY KEY,
    userAccount  VARCHAR(256) NOT NULL,
    userPassword VARCHAR(512) NOT NULL,
    userName     VARCHAR(256),
    userAvatar   VARCHAR(1024),
    userProfile  VARCHAR(512),
    userRole     VARCHAR(256) DEFAULT 'user' NOT NULL,
    editTime     TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    createTime   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updateTime   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    isDelete     SMALLINT DEFAULT 0 NOT NULL,
    CONSTRAINT uk_userAccount UNIQUE (userAccount)
);

-- 添加注释
COMMENT ON TABLE "user" IS '用户表';
COMMENT ON COLUMN "user".id IS 'id';
COMMENT ON COLUMN "user".userAccount IS '账号';
COMMENT ON COLUMN "user".userPassword IS '密码';
COMMENT ON COLUMN "user".userName IS '用户昵称';
COMMENT ON COLUMN "user".userAvatar IS '用户头像';
COMMENT ON COLUMN "user".userProfile IS '用户简介';
COMMENT ON COLUMN "user".userRole IS '用户角色：user/admin';
COMMENT ON COLUMN "user".editTime IS '编辑时间';
COMMENT ON COLUMN "user".createTime IS '创建时间';
COMMENT ON COLUMN "user".updateTime IS '更新时间';
COMMENT ON COLUMN "user".isDelete IS '是否删除';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_userName ON "user" (userName);

-- 创建更新时间自动更新的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updateTime = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器，自动更新 updateTime
CREATE TRIGGER update_user_updated_at
    BEFORE UPDATE ON "user"
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

