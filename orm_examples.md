# ORM 操作示例

## 查询操作

### 基本查询
```python
# 查询所有用户
db.execute(select(User))

# 根据条件查询
db.execute(select(User).filter(User.username == username))

# 多个条件
db.execute(select(User).filter(User.username == username, User.is_active == True))

# 使用 where
db.execute(select(User).where(User.id == user_id))

# 查询单个字段
db.execute(select(User.username))

# 查询多个字段
db.execute(select(User.id, User.username, User.email))
```

### 条件查询
```python
# 等于
db.execute(select(User).filter(User.status == "active"))

# 不等于
db.execute(select(User).filter(User.status != "inactive"))

# 大于/小于
db.execute(select(User).filter(User.age > 18))
db.execute(select(User).filter(User.created_at < datetime.now()))

# 包含
db.execute(select(User).filter(User.username.in_(["admin", "user"])))

# LIKE 查询
db.execute(select(User).filter(User.username.like("%admin%")))

# 空值检查
db.execute(select(User).filter(User.deleted_at.is_(None)))
db.execute(select(User).filter(User.deleted_at.is_not(None)))
```

### 排序和分页
```python
# 排序
db.execute(select(User).order_by(User.created_at.desc()))
db.execute(select(User).order_by(User.created_at.asc(), User.id.desc()))

# 限制数量
db.execute(select(User).limit(10))

# 跳过记录
db.execute(select(User).offset(10))

# 分页
db.execute(select(User).limit(10).offset(20))
```

### 关联查询
```python
# JOIN 查询
db.execute(select(User, Profile).join(Profile, User.id == Profile.user_id))

# LEFT JOIN
db.execute(select(User, Profile).outerjoin(Profile, User.id == Profile.user_id))

# 关联过滤
db.execute(select(User).join(Order).filter(Order.total > 100))
```

### 聚合查询
```python
# 计数
db.execute(select(func.count(User.id)))

# 求和
db.execute(select(func.sum(Order.total)))

# 平均值
db.execute(select(func.avg(Order.total)))

# 最大值/最小值
db.execute(select(func.max(User.created_at)))
db.execute(select(func.min(User.created_at)))

# GROUP BY
db.execute(select(User.status, func.count(User.id)).group_by(User.status))
```

### 子查询
```python
# 子查询
subquery = select(Order.user_id).filter(Order.total > 100).subquery()
db.execute(select(User).filter(User.id.in_(subquery)))
```

## 插入操作

```python
# 插入单条记录
db.execute(insert(User).values(username="admin", email="admin@example.com"))

# 插入多条记录
db.execute(insert(User).values([
    {"username": "user1", "email": "user1@example.com"},
    {"username": "user2", "email": "user2@example.com"}
]))

# 插入并返回
db.execute(insert(User).values(username="admin").returning(User.id))
```

## 更新操作

```python
# 更新单条记录
db.execute(update(User).where(User.id == user_id).values(username="new_username"))

# 更新多条记录
db.execute(update(User).where(User.status == "inactive").values(is_active=False))

# 更新并返回
db.execute(update(User).where(User.id == user_id).values(email="new@example.com").returning(User))
```

## 删除操作

```python
# 删除单条记录
db.execute(delete(User).where(User.id == user_id))

# 删除多条记录
db.execute(delete(User).where(User.status == "deleted"))

# 软删除（更新）
db.execute(update(User).where(User.id == user_id).values(deleted_at=datetime.now()))
```

## 复杂查询

### 联合查询
```python
# UNION
query1 = select(User.id, User.username).filter(User.role == "admin")
query2 = select(User.id, User.username).filter(User.role == "user")
db.execute(union(query1, query2))
```

### 存在性检查
```python
# EXISTS
subquery = select(Order.id).where(Order.user_id == User.id).exists()
db.execute(select(User).filter(subquery))
```

### 条件表达式
```python
# CASE WHEN
db.execute(select(
    User.id,
    case((User.status == "active", "Active"), else_="Inactive").label("status_label")
))
```

## 事务操作

```python
# 开始事务
with db.begin():
    db.execute(insert(User).values(username="user1"))
    db.execute(insert(Profile).values(user_id=user_id, bio="Bio"))
```

## 常用组合

```python
# 查询并获取结果
result = db.execute(select(User).filter(User.username == username))
user = result.scalar_one_or_none()

# 查询多条
result = db.execute(select(User).limit(10))
users = result.scalars().all()

# 查询第一条
result = db.execute(select(User).filter(User.id == user_id))
user = result.scalar_one()

# 查询是否存在
result = db.execute(select(func.count(User.id)).filter(User.username == username))
exists = result.scalar() > 0
```

