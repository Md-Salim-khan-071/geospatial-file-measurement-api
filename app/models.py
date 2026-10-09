from sqlalchemy import Column, String, Integer, JSON
from app.database import Base


class GeospatialFile(Base):
    __tablename__ = "geospatial_files"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    crs = Column(String, nullable=True)
    feature_count = Column(Integer, default=0)
    status = Column(String, default="COMPLETED")
    measurements = Column(JSON, nullable=True)
