from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poc.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


# Association table for coversLocation relationship
covers_location = db.Table(
    'covers_location',
    db.Column('location_id', db.Integer, db.ForeignKey('location.id'), primary_key=True),
    db.Column('covered_location_id', db.Integer, db.ForeignKey('location.id'), primary_key=True)
)


class Carrier(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    reliability = Column(Float)
    type = Column(String)
    supports_dangerous_goods = Column(Boolean, default=False)
    supports_freezing = Column(Boolean, default=False)
    routes = relationship('Route', back_populates='carrier')


class Location(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String)
    located_in_country = Column(String)
    supports_freezing = Column(Boolean, default=False)
    supports_storage = Column(Boolean, default=False)
    supports_dangerous_goods = Column(Boolean, default=False)
    covered_locations = relationship(
        'Location',
        secondary=covers_location,
        primaryjoin=id == covers_location.c.location_id,
        secondaryjoin=id == covers_location.c.covered_location_id,
        backref='covering_locations'
    )


class Route(db.Model):
    id = Column(Integer, primary_key=True)
    origin_id = Column(Integer, ForeignKey('location.id'))
    destination_id = Column(Integer, ForeignKey('location.id'))
    carrier_id = Column(Integer, ForeignKey('carrier.id'))
    base_cost = Column(Float)
    lead_time = Column(Float)
    transport_mode = Column(String)
    supports_dangerous_goods = Column(Boolean, default=False)
    supports_freezing = Column(Boolean, default=False)
    type = Column(String)

    origin = relationship('Location', foreign_keys=[origin_id])
    destination = relationship('Location', foreign_keys=[destination_id])
    carrier = relationship('Carrier', back_populates='routes')
    schedules = relationship('Schedule', back_populates='route')
    cost_items = relationship('CostItem', back_populates='route')


class Schedule(db.Model):
    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey('route.id'))
    departure_day = Column(String)
    frequency = Column(Integer)
    cutoff_day_offset = Column(Integer)
    cutoff_hour = Column(Integer)
    type = Column(String)

    route = relationship('Route', back_populates='schedules')


class Shipment(db.Model):
    id = Column(Integer, primary_key=True)
    origin_id = Column(Integer, ForeignKey('location.id'))
    destination_id = Column(Integer, ForeignKey('location.id'))
    weight = Column(Float)
    is_dangerous = Column(Boolean, default=False)
    requires_freezing = Column(Boolean, default=False)
    deadline = Column(DateTime)
    incoterms = Column(String)
    type = Column(String)

    origin = relationship('Location', foreign_keys=[origin_id])
    destination = relationship('Location', foreign_keys=[destination_id])


class CostItem(db.Model):
    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey('route.id'))
    cost_type = Column(String)
    amount = Column(Float)
    trigger_type = Column(String)
    trigger_operator = Column(String)
    trigger_value = Column(Float)
    type = Column(String)

    route = relationship('Route', back_populates='cost_items')


# Utility functions

def model_to_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def create_crud_endpoints(model, endpoint):
    model_name = model.__name__.lower()

    @app.route(f"/{endpoint}", methods=['POST'])
    def create_item():
        data = request.json or {}
        item = model(**data)
        db.session.add(item)
        db.session.commit()
        return jsonify(model_to_dict(item)), 201

    @app.route(f"/{endpoint}", methods=['GET'])
    def list_items():
        items = model.query.all()
        return jsonify([model_to_dict(i) for i in items])

    @app.route(f"/{endpoint}/<int:item_id>", methods=['GET'])
    def get_item(item_id):
        item = model.query.get_or_404(item_id)
        return jsonify(model_to_dict(item))

    @app.route(f"/{endpoint}/<int:item_id>", methods=['PUT'])
    def update_item(item_id):
        item = model.query.get_or_404(item_id)
        data = request.json or {}
        for key, value in data.items():
            setattr(item, key, value)
        db.session.commit()
        return jsonify(model_to_dict(item))

    @app.route(f"/{endpoint}/<int:item_id>", methods=['DELETE'])
    def delete_item(item_id):
        item = model.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return '', 204


create_crud_endpoints(Carrier, 'carriers')
create_crud_endpoints(Location, 'locations')
create_crud_endpoints(Route, 'routes')
create_crud_endpoints(Schedule, 'schedules')
create_crud_endpoints(Shipment, 'shipments')
create_crud_endpoints(CostItem, 'costitems')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
