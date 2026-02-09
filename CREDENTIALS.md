# 默认账号密码

## 管理员账号

| 字段 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `admin` |
| 权限 | 超级管理员 |

## 修改方式

密码存储在数据库中，使用 bcrypt 算法加密。

如需修改密码，可以通过以下方式：

1. **直接修改数据库**：
   ```python
   import sqlite3
   import bcrypt

   conn = sqlite3.connect('backend/data/sqlite.db')
   cursor = conn.cursor()

   new_password = 'your_new_password'
   hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

   cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (hashed.decode(), 'admin'))
   conn.commit()
   conn.close()
   ```

2. **通过 API 修改**（需要登录后）：
   - PUT `/api/auth/password`
   - Body: `{"old_password": "admin", "new_password": "your_new_password"}`

## 注意事项

- 生产环境请务必修改默认密码
- 首次登录后建议启用 2FA 双因素认证
