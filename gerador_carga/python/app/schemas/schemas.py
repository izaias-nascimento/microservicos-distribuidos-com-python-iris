import os
from typing import Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, field_validator
from typing import Optional
load_dotenv()


# ------------ MODELS ------------

class Team(BaseModel):
    id: int
    conference: Optional[str] = None
    division: Optional[str] = None
    city: Optional[str] = None
    name: str
    full_name: str
    abbreviation: str

    @field_validator("conference", "division", "city", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v


class Game(BaseModel):
    id: int
    date: str
    season: int
    status: str
    period: int
    postseason: bool
    home_team_score: int
    visitor_team_score: int
    home_team: Team
    visitor_team: Team

    def to_flat(self) -> "GameFlat":
        return GameFlat(
            id=self.id,
            date=self.date,
            season=self.season,
            status=self.status,
            period=self.period,
            postseason=self.postseason,
            home_team_id=self.home_team.id,
            home_team_full_name=self.home_team.full_name,
            home_team_abbr=self.home_team.abbreviation,
            home_team_conf=self.home_team.conference,
            home_team_div=self.home_team.division,
            home_team_score=self.home_team_score,
            visitor_team_id=self.visitor_team.id,
            visitor_team_full_name=self.visitor_team.full_name,
            visitor_team_abbr=self.visitor_team.abbreviation,
            visitor_team_conf=self.visitor_team.conference,
            visitor_team_div=self.visitor_team.division,
            visitor_team_score=self.visitor_team_score,
        )


class GameFlat(BaseModel):
    id: int
    date: str
    season: int
    status: str
    period: int
    postseason: bool

    home_team_id: int
    home_team_full_name: str
    home_team_abbr: str
    home_team_conf: Optional[str] = None
    home_team_div: Optional[str] = None
    home_team_score: int

    visitor_team_id: int
    visitor_team_full_name: str
    visitor_team_abbr: str
    visitor_team_conf: Optional[str] = None
    visitor_team_div: Optional[str] = None
    visitor_team_score: int


# ------------ FUNÇÃO DE SPLIT E VALIDAÇÃO ------------

TEAMS_URL = os.getenv("TEAMS_URL")

GAMES_URL = os.getenv("GAMES_URL")


def split_and_models(results: Dict[str, Any]):
    teams_raw = results.get(TEAMS_URL, {}).get("data", [])
    games_raw = results.get(GAMES_URL, {}).get("data", [])

    teams = [Team.model_validate(t) for t in teams_raw]
    games = [Game.model_validate(g) for g in games_raw]
    games_flat = [g.to_flat() for g in games]
    team_by_id = {t.id: t for t in teams}

    return {
        "teams": teams,
        "games": games,
        "games_flat": games_flat,
        "team_by_id": team_by_id,
    }
