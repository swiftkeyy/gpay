"""Manage user roles: admins, moderators, security, sellers."""
import sys
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
sync_engine = create_engine(settings.sync_database_url, echo=False)

ROLES = {
    'super_admin': '👑 Супер Админ (полный доступ)',
    'admin': '⚙️ Админ (управление контентом)',
    'moderator': '🛡️ Модератор (модерация отзывов и споров)',
    'security': '🔒 Служба безопасности (блокировка пользователей)'
}

def add_role(telegram_id: int, role: str):
    """Add admin role to user by telegram_id."""
    if role not in ROLES:
        print(f"❌ Invalid role: {role}")
        print(f"   Available roles: {', '.join(ROLES.keys())}")
        return False
    
    print(f"🔧 Adding role '{role}' to user with telegram_id={telegram_id}...")
    
    with sync_engine.begin() as conn:
        # Check if user exists
        result = conn.execute(
            text("SELECT id, username, first_name FROM users WHERE telegram_id = :telegram_id"),
            {"telegram_id": telegram_id}
        )
        user = result.fetchone()
        
        if not user:
            print(f"❌ User with telegram_id={telegram_id} not found!")
            print("   User must authenticate in the app first.")
            return False
        
        user_id, username, first_name = user
        print(f"✅ Found user: {first_name or username or telegram_id} (id={user_id})")
        
        # Check if admin record already exists
        result = conn.execute(
            text("SELECT id, role, is_active FROM admins WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        admin = result.fetchone()
        
        if admin:
            admin_id, current_role, is_active = admin
            if is_active and current_role == role:
                print(f"ℹ️  User already has role: {ROLES[role]}")
                return True
            else:
                # Update role
                conn.execute(
                    text("UPDATE admins SET role = :role, is_active = true WHERE id = :admin_id"),
                    {"role": role, "admin_id": admin_id}
                )
                print(f"✅ Role updated: {ROLES[current_role]} → {ROLES[role]}")
                return True
        
        # Create new admin record
        conn.execute(
            text("""
                INSERT INTO admins (user_id, role, is_active, created_at)
                VALUES (:user_id, :role, true, NOW())
            """),
            {"user_id": user_id, "role": role}
        )
        print(f"✅ Role granted: {ROLES[role]}")
        return True

def add_seller(telegram_id: int):
    """Add seller status to user."""
    print(f"🏪 Adding seller status to user with telegram_id={telegram_id}...")
    
    with sync_engine.begin() as conn:
        # Check if user exists
        result = conn.execute(
            text("SELECT id, username, first_name FROM users WHERE telegram_id = :telegram_id"),
            {"telegram_id": telegram_id}
        )
        user = result.fetchone()
        
        if not user:
            print(f"❌ User with telegram_id={telegram_id} not found!")
            print("   User must authenticate in the app first.")
            return False
        
        user_id, username, first_name = user
        print(f"✅ Found user: {first_name or username or telegram_id} (id={user_id})")
        
        # Check if seller record already exists
        result = conn.execute(
            text("SELECT id, is_active FROM sellers WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        seller = result.fetchone()
        
        if seller:
            seller_id, is_active = seller
            if is_active:
                print(f"ℹ️  User is already an active seller")
                return True
            else:
                # Reactivate seller
                conn.execute(
                    text("UPDATE sellers SET is_active = true WHERE id = :seller_id"),
                    {"seller_id": seller_id}
                )
                print(f"✅ Seller status reactivated")
                return True
        
        # Create new seller record
        conn.execute(
            text("""
                INSERT INTO sellers (user_id, is_active, created_at)
                VALUES (:user_id, true, NOW())
            """),
            {"user_id": user_id}
        )
        print(f"✅ Seller status granted successfully!")
        return True

def remove_role(telegram_id: int):
    """Remove admin role from user."""
    print(f"🗑️ Removing admin role from user with telegram_id={telegram_id}...")
    
    with sync_engine.begin() as conn:
        # Check if user exists
        result = conn.execute(
            text("SELECT id, username, first_name FROM users WHERE telegram_id = :telegram_id"),
            {"telegram_id": telegram_id}
        )
        user = result.fetchone()
        
        if not user:
            print(f"❌ User with telegram_id={telegram_id} not found!")
            return False
        
        user_id, username, first_name = user
        print(f"✅ Found user: {first_name or username or telegram_id} (id={user_id})")
        
        # Deactivate admin
        result = conn.execute(
            text("UPDATE admins SET is_active = false WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        
        if result.rowcount > 0:
            print(f"✅ Admin role removed")
            return True
        else:
            print(f"ℹ️  User doesn't have admin role")
            return True

def list_admins():
    """List all admins."""
    print("📋 Current admins:\n")
    
    with sync_engine.begin() as conn:
        result = conn.execute(text("""
            SELECT u.telegram_id, u.username, u.first_name, a.role, a.is_active
            FROM admins a
            JOIN users u ON u.id = a.user_id
            ORDER BY a.role, u.telegram_id
        """))
        
        admins = result.fetchall()
        
        if not admins:
            print("   No admins found")
            return
        
        for telegram_id, username, first_name, role, is_active in admins:
            status = "✅" if is_active else "❌"
            name = first_name or username or f"user_{telegram_id}"
            print(f"   {status} {ROLES.get(role, role)}: {name} (@{username or 'no_username'}) - {telegram_id}")

def print_usage():
    """Print usage instructions."""
    print("""
🎮 Game Pay - Role Management Tool

Usage:
  python add_admin.py add <telegram_id> <role>     - Add admin role
  python add_admin.py seller <telegram_id>          - Add seller status
  python add_admin.py remove <telegram_id>          - Remove admin role
  python add_admin.py list                          - List all admins

Available roles:
  super_admin  - 👑 Супер Админ (полный доступ)
  admin        - ⚙️ Админ (управление контентом)
  moderator    - 🛡️ Модератор (модерация отзывов и споров)
  security     - 🔒 Служба безопасности (блокировка пользователей)

Examples:
  python add_admin.py add 123456789 super_admin
  python add_admin.py add 987654321 moderator
  python add_admin.py seller 555555555
  python add_admin.py remove 123456789
  python add_admin.py list
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "add":
            if len(sys.argv) < 4:
                print("❌ Missing arguments")
                print("Usage: python add_admin.py add <telegram_id> <role>")
                sys.exit(1)
            telegram_id = int(sys.argv[2])
            role = sys.argv[3].lower()
            success = add_role(telegram_id, role)
            sys.exit(0 if success else 1)
        
        elif command == "seller":
            if len(sys.argv) < 3:
                print("❌ Missing telegram_id")
                print("Usage: python add_admin.py seller <telegram_id>")
                sys.exit(1)
            telegram_id = int(sys.argv[2])
            success = add_seller(telegram_id)
            sys.exit(0 if success else 1)
        
        elif command == "remove":
            if len(sys.argv) < 3:
                print("❌ Missing telegram_id")
                print("Usage: python add_admin.py remove <telegram_id>")
                sys.exit(1)
            telegram_id = int(sys.argv[2])
            success = remove_role(telegram_id)
            sys.exit(0 if success else 1)
        
        elif command == "list":
            list_admins()
            sys.exit(0)
        
        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
            sys.exit(1)
    
    except ValueError:
        print("❌ Invalid telegram_id. Must be a number.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
