from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

# Initialize the SQLAlchemy extension
db = SQLAlchemy()

class TestResult(db.Model):
    """
    Represents the overall result of a single DNS test.
    """
    __tablename__ = 'test_results'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    domain = db.Column(db.String(255), nullable=False)
    record_type = db.Column(db.String(10), nullable=False)
    query_time_ms = db.Column(db.Integer)
    status = db.Column(db.String(50))

    # This establishes the one-to-many relationship to DNSRecord
    records = relationship("DNSRecord", back_populates="test_result", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<TestResult {self.id} for {self.domain}>'

class DNSRecord(db.Model):
    """
    Represents a single record from the ANSWER SECTION of a DNS response.
    """
    __tablename__ = 'dns_records'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    ttl = db.Column(db.Integer)
    record_class = db.Column(db.String(10))
    record_type = db.Column(db.String(10))
    data = db.Column(db.String(255))

    # Foreign key to link back to the parent TestResult
    test_result_id = db.Column(db.Integer, db.ForeignKey('test_results.id'), nullable=False)

    # This establishes the many-to-one relationship to TestResult
    test_result = relationship("TestResult", back_populates="records")

    def __repr__(self):
        return f'<DNSRecord {self.name} {self.record_type} {self.data}>'