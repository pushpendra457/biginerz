from contextlib import asynccontextmanager
from fastapi import FastAPI, Request ,HTTPException,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

