from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    session_id = Column(String(255))

class Tracker(Base):
    __tablename__ = 'trackers'

    tracker_id = Column(Integer, primary_key=True)
    alias = Column(String(255))
    description = Column(Text)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    tracker_type = Column(String(255), nullable=False)
    timing_enabled = Column(Boolean, nullable=False)
    status = Column(String(255), nullable=False)
    record_num = Column(Integer, default=0)

class RedirectLink(Base):
    __tablename__ = 'redirect_links'

    redirect_link_id = Column(Integer, primary_key=True)
    tracker_id = Column(Integer, ForeignKey('trackers.tracker_id'))
    target_url = Column(Text, nullable=False)

class TrackerRecord(Base):
    __tablename__ = 'tracker_records'

    record_id = Column(Integer, primary_key=True)
    tracker_id = Column(Integer, ForeignKey('trackers.tracker_id'))
    access_time = Column(TIMESTAMP, nullable=False)
    access_ip = Column(INET, nullable=False)
    country = Column(String(255))
    city = Column(String(255))
    isp = Column(String(255))
    request_header = Column(Text)

class TimingRecord(Base):
    __tablename__ = 'timing_records'

    timing_record_id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey('tracker_records.record_id'))
    last_access_time = Column(TIMESTAMP, nullable=False)
    redirect_count = Column(Integer, nullable=False)

class UserActivity(Base):
    __tablename__ = 'user_activity'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(255))
    tracker_count = Column(Integer)
    record_count = Column(Integer)
