import argparse
from datetime import datetime
from marc_db.db import get_session
from marc_db.models import Aliquot, Base, Isolate
from sqlalchemy.orm import Session


isolate1 = Isolate(subject_id=1, specimen_id=1, source="blood culture", suspected_organism="K. pneumonia", special_collection="none", received_date=datetime(2021, 1, 1), cryobanking_date=datetime(2021, 1, 2))
isolate2 = Isolate(subject_id=1, specimen_id=2)

aliquot1 = Aliquot(isolate_id=1, tube_barcode="123", box_name="box1")
aliquot2 = Aliquot(isolate_id=1, tube_barcode="124", box_name="box1")
aliquot3 = Aliquot(isolate_id=2, tube_barcode="125", box_name="box1")
aliquot4 = Aliquot(isolate_id=2, tube_barcode="126", box_name="box1")


def fill_mock_db(session: Session = get_session()):
    # Check that db is an empty test db
    assert len(session.query(Isolate).all()) == 0, "Database is not empty, I can only add test data to an empty database"

    session.add_all([isolate1, isolate2, aliquot1, aliquot2, aliquot3, aliquot4])
    session.commit()


def fill_mock_db_cli(argv):
    parser = argparse.ArgumentParser(description="Fill mock values into an empty db (for testing).")
    parser.add_argument("--db_url", default="sqlite:///:memory:", help="The database URL.")
    args = parser.parse_args(argv)

    fill_mock_db(get_session(args.db_url))