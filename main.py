from db import PromptDB
from fastapi import FastAPI, Request, Response

db = PromptDB()
app = FastAPI()
