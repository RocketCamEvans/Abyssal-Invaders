from pydantic import BaseModel, Field

# Player creation (name is optional, default handled in route)
class PlayerCreateRequest(BaseModel):
	name: str = Field(..., min_length=1, max_length=50)

# Player status, movement, stats, delete, encounter ally (all require session_id)
class PlayerSessionRequest(BaseModel):
	session_id: str = Field(..., min_length=8)

class PlayerMoveRequest(PlayerSessionRequest):
	direction: str = Field(..., pattern=r"^(north|south|east|west|up)$")

# Combat endpoints
class CombatAttackRequest(PlayerSessionRequest):
	action: str
	use_ally: bool

class CombatUseAllyRequest(PlayerSessionRequest):
	ally_index: int
	enemy_data: dict

class CombatFleeRequest(PlayerSessionRequest):
	enemy_data: dict

# Score submission
class ScoreSubmitRequest(PlayerSessionRequest):
	gold: int = Field(..., ge=0)
