from app import db


class SystemConfig(db.Model):
    __tablename__ = 'system_configs'

    config_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_key = db.Column(db.String(50), unique=True, nullable=False)
    config_value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'config_id': self.config_id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'description': self.description
        }