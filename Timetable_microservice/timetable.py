from fastapi import APIRouter, HTTPException

from starlette import status
import requests as req

from models import Timetable, UpdateTimetable, TimePeriod, TimeSelect
import db_manager

timetable_app = APIRouter()

