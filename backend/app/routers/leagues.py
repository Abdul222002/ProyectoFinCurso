"""
Router de Ligas — Crear, Invitar, Unirse, Clasificación
Con generación automática de equipo + 15 jugadores aleatorios al unirse
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from typing import List
import uuid
import random

from app.core.database import get_db
from app.models.models import (
    User, League, LeagueMember, LeagueInvitation, InvitationStatus,
    Team, Player, UserCard, Position
)
from app.schemas.league import (
    LeagueCreate, LeagueUpdate, LeagueResponse, LeagueListResponse,
    LeagueDetailResponse, LeagueMemberResponse,
    InvitationCreate, InvitationResponse
)
from app.routers.auth import get_current_user

router = APIRouter()


def _generate_invite_code() -> str:
    """Genera un código corto de invitación"""
    return uuid.uuid4().hex[:8].upper()


def _create_team_for_league(user: User, league: League, db: Session) -> Team:
    """
    Crea un equipo automáticamente para un usuario en una liga
    con 15 jugadores aleatorios (2 GK, 4 DEF, 4 MID, 3 FWD + 2 random)
    Los 11 primeros son titulares.
    """
    # Crear equipo
    team = Team(
        name=f"{user.username} FC",
        user_id=user.id,
        league_id=league.id,
        active_formation="4-4-2"
    )
    db.add(team)
    db.flush()  # Para obtener team.id

    # Obtener jugadores aleatorios por posición
    gk_players = db.query(Player).filter(Player.position == Position.GK).order_by(func.rand()).limit(2).all()
    def_players = db.query(Player).filter(Player.position == Position.DEF).order_by(func.rand()).limit(4).all()
    mid_players = db.query(Player).filter(Player.position == Position.MID).order_by(func.rand()).limit(4).all()
    fwd_players = db.query(Player).filter(Player.position == Position.FWD).order_by(func.rand()).limit(3).all()

    # 2 suplentes extra aleatorios (de cualquier posición, evitando duplicados)
    assigned_ids = [p.id for p in gk_players + def_players + mid_players + fwd_players]
    extra_players = db.query(Player).filter(
        ~Player.id.in_(assigned_ids)
    ).order_by(func.rand()).limit(2).all()

    all_players = gk_players + def_players + mid_players + fwd_players + extra_players

    # Crear cartas — los 11 primeros son titulares
    total_ovr = 0
    lineup_count = 0
    for i, player in enumerate(all_players):
        is_lineup = i < 11  # Primeros 11 = titulares
        card = UserCard(
            user_id=user.id,
            player_id=player.id,
            team_id=team.id,
            current_overall=player.overall_rating,
            is_in_lineup=is_lineup,
            is_tradeable=True
        )
        db.add(card)
        if is_lineup:
            total_ovr += player.overall_rating
            lineup_count += 1

    # Calcular OVR del equipo
    if lineup_count > 0:
        team.overall_rating = total_ovr / lineup_count

    return team


def _league_to_response(league: League) -> LeagueResponse:
    return LeagueResponse(
        id=league.id,
        name=league.name,
        description=league.description,
        owner_id=league.owner_id,
        owner_username=league.owner.username,
        max_members=league.max_members,
        member_count=league.member_count,
        is_public=league.is_public,
        invite_code=league.invite_code,
        created_at=league.created_at
    )


def _member_to_response(member: LeagueMember) -> LeagueMemberResponse:
    return LeagueMemberResponse(
        id=member.id,
        user_id=member.user_id,
        username=member.user.username,
        league_points=member.league_points,
        is_admin=member.is_admin,
        joined_at=member.joined_at
    )


def _invitation_to_response(inv: LeagueInvitation) -> InvitationResponse:
    return InvitationResponse(
        id=inv.id,
        league_id=inv.league_id,
        league_name=inv.league.name,
        invited_by_username=inv.invited_by.username,
        invited_email=inv.invited_email,
        invited_username=inv.invited_user.username if inv.invited_user else None,
        status=inv.status.value,
        created_at=inv.created_at
    )


# ==========================================
# Fixed-path routes BEFORE parameterized /{league_id}
# ==========================================

@router.get("/invitations/pending", response_model=List[InvitationResponse])
async def my_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mis invitaciones pendientes"""
    invitations = db.query(LeagueInvitation).filter(
        LeagueInvitation.invited_user_id == current_user.id,
        LeagueInvitation.status == InvitationStatus.PENDING
    ).all()
    return [_invitation_to_response(inv) for inv in invitations]


@router.post("/invitations/{invitation_id}/accept", response_model=LeagueListResponse)
async def accept_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aceptar una invitación — crea equipo automáticamente"""
    invitation = db.query(LeagueInvitation).filter(
        LeagueInvitation.id == invitation_id,
        LeagueInvitation.invited_user_id == current_user.id,
        LeagueInvitation.status == InvitationStatus.PENDING
    ).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitación no encontrada")

    league = invitation.league

    if league.member_count >= league.max_members:
        raise HTTPException(status_code=400, detail="La liga está llena")

    # Aceptar invitación
    invitation.status = InvitationStatus.ACCEPTED

    # Crear miembro
    member = LeagueMember(
        league_id=league.id,
        user_id=current_user.id
    )
    db.add(member)

    # Auto-crear equipo con 15 jugadores aleatorios
    _create_team_for_league(current_user, league, db)

    db.commit()
    db.refresh(league)

    return LeagueListResponse(
        id=league.id,
        name=league.name,
        owner_username=league.owner.username,
        member_count=league.member_count,
        max_members=league.max_members,
        is_public=league.is_public
    )


@router.post("/invitations/{invitation_id}/reject")
async def reject_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rechazar una invitación"""
    invitation = db.query(LeagueInvitation).filter(
        LeagueInvitation.id == invitation_id,
        LeagueInvitation.invited_user_id == current_user.id,
        LeagueInvitation.status == InvitationStatus.PENDING
    ).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitación no encontrada")

    invitation.status = InvitationStatus.REJECTED
    db.commit()
    return {"message": "Invitación rechazada"}


@router.post("/join/{invite_code}", response_model=LeagueListResponse)
async def join_by_code(
    invite_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unirse a una liga por código — crea equipo automáticamente"""
    league = db.query(League).filter(League.invite_code == invite_code).first()
    if not league:
        raise HTTPException(status_code=404, detail="Código de invitación inválido")

    already = db.query(LeagueMember).filter(
        LeagueMember.league_id == league.id,
        LeagueMember.user_id == current_user.id
    ).first()
    if already:
        raise HTTPException(status_code=400, detail="Ya eres miembro de esta liga")

    if league.member_count >= league.max_members:
        raise HTTPException(status_code=400, detail="La liga está llena")

    # Crear miembro
    member = LeagueMember(
        league_id=league.id,
        user_id=current_user.id
    )
    db.add(member)

    # Auto-crear equipo con 15 jugadores aleatorios
    _create_team_for_league(current_user, league, db)

    db.commit()
    db.refresh(league)

    return LeagueListResponse(
        id=league.id,
        name=league.name,
        owner_username=league.owner.username,
        member_count=league.member_count,
        max_members=league.max_members,
        is_public=league.is_public
    )


# ==========================================
# CRUD DE LIGAS
# ==========================================

@router.post("/", response_model=LeagueResponse, status_code=201)
async def create_league(
    data: LeagueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear una nueva liga — auto-crea equipo con 15 jugadores aleatorios"""
    league = League(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
        max_members=data.max_members,
        is_public=data.is_public,
        invite_code=_generate_invite_code()
    )
    db.add(league)
    db.flush()

    # El creador se une como admin
    member = LeagueMember(
        league_id=league.id,
        user_id=current_user.id,
        is_admin=True
    )
    db.add(member)

    # Auto-crear equipo con 15 jugadores aleatorios
    _create_team_for_league(current_user, league, db)

    db.commit()
    db.refresh(league)

    return _league_to_response(league)


@router.get("/", response_model=List[LeagueListResponse])
async def my_leagues(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar las ligas del usuario actual"""
    memberships = db.query(LeagueMember).filter(
        LeagueMember.user_id == current_user.id
    ).all()

    result = []
    for m in memberships:
        league = m.league
        result.append(LeagueListResponse(
            id=league.id,
            name=league.name,
            owner_username=league.owner.username,
            member_count=league.member_count,
            max_members=league.max_members,
            is_public=league.is_public
        ))
    return result


@router.get("/{league_id}", response_model=LeagueDetailResponse)
async def get_league_detail(
    league_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detalle de liga con clasificación de miembros"""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="Liga no encontrada")

    is_member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    if not is_member and not league.is_public:
        raise HTTPException(status_code=403, detail="No eres miembro de esta liga")

    members_sorted = sorted(league.members, key=lambda m: m.league_points, reverse=True)

    return LeagueDetailResponse(
        id=league.id,
        name=league.name,
        description=league.description,
        owner_id=league.owner_id,
        owner_username=league.owner.username,
        max_members=league.max_members,
        member_count=league.member_count,
        is_public=league.is_public,
        invite_code=league.invite_code,
        created_at=league.created_at,
        members=[_member_to_response(m) for m in members_sorted]
    )


@router.post("/{league_id}/invite", response_model=InvitationResponse, status_code=201)
async def invite_to_league(
    league_id: int,
    data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invitar a un usuario a la liga"""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="Liga no encontrada")

    membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="No eres miembro de esta liga")

    invited_user = None
    invited_email = data.email

    if data.username:
        invited_user = db.query(User).filter(User.username == data.username).first()
        if not invited_user:
            raise HTTPException(status_code=404, detail=f"Usuario '{data.username}' no encontrado")
        invited_email = invited_user.email

        already_member = db.query(LeagueMember).filter(
            LeagueMember.league_id == league_id,
            LeagueMember.user_id == invited_user.id
        ).first()
        if already_member:
            raise HTTPException(status_code=400, detail="Este usuario ya es miembro de la liga")

        existing = db.query(LeagueInvitation).filter(
            LeagueInvitation.league_id == league_id,
            LeagueInvitation.invited_user_id == invited_user.id,
            LeagueInvitation.status == InvitationStatus.PENDING
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ya hay una invitación pendiente para este usuario")

    elif not data.email:
        raise HTTPException(status_code=400, detail="Debes especificar username o email")

    invitation = LeagueInvitation(
        league_id=league_id,
        invited_by_id=current_user.id,
        invited_user_id=invited_user.id if invited_user else None,
        invited_email=invited_email,
        token=uuid.uuid4().hex[:16]
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    return _invitation_to_response(invitation)


# ==========================================
# SALIR DE LIGA
# ==========================================

@router.delete("/{league_id}/leave")
async def leave_league(
    league_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Salir de una liga"""
    membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="No eres miembro de esta liga")

    league = db.query(League).filter(League.id == league_id).first()

    if league.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="El creador no puede abandonar la liga.")

    # Eliminar equipo y cartas de esta liga
    team = db.query(Team).filter(
        Team.user_id == current_user.id,
        Team.league_id == league_id
    ).first()
    if team:
        db.query(UserCard).filter(UserCard.team_id == team.id).delete()
        db.delete(team)

    db.delete(membership)
    db.commit()
    return {"message": "Has salido de la liga"}
