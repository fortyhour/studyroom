from app import db


class Permission(db.Model):
    __tablename__ = 'permissions'

    perm_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    perm_name = db.Column(db.String(50), nullable=False)
    perm_code = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'perm_id': self.perm_id,
            'perm_name': self.perm_name,
            'perm_code': self.perm_code,
            'description': self.description
        }