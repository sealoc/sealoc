"""
Module for database types.
"""

import typing

import sqlalchemy as sqla
import sqlmodel as sqlm


Engine: typing.TypeAlias = sqla.engine.base.Engine
Session: typing.TypeAlias = sqlm.Session
