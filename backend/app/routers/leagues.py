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
    Team, Player, UserCard, Position, CardRarity,
    SystemOffer, MarketListing, MarketAuction, AuctionSlot, AuctionBid,
    ListingBid, PackOpening, GameweekLineup, GameweekLineupPlayer, PackOpeningCard,
    ArenaBattle, Notification
)
from app.schemas.league import (
    LeagueCreate, LeagueUpdate, LeagueResponse, LeagueListResponse,
    LeagueDetailResponse, LeagueMemberResponse,
    InvitationCreate, InvitationResponse,
    LeagueJoinResponse, AssignedPlayerCard
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

    # IDs de jugadores ya poseídos en la liga para evitar duplicados globales
    owned_player_ids = db.query(UserCard.player_id).filter(UserCard.league_id == league.id).all()
    owned_player_ids = [r[0] for r in owned_player_ids]

    # Obtener jugadores aleatorios por posición, EXCLUYENDO LEYENDAS y YA POSEÍDOS
    gk_players = db.query(Player).filter(
        Player.position == Position.GK,
        Player.base_rarity != CardRarity.LEGEND,
        ~Player.id.in_(owned_player_ids)
    ).order_by(func.rand()).limit(2).all()
    
    def_players = db.query(Player).filter(
        Player.position == Position.DEF,
        Player.base_rarity != CardRarity.LEGEND,
        ~Player.id.in_(owned_player_ids + [p.id for p in gk_players])
    ).order_by(func.rand()).limit(4).all()
    
    mid_players = db.query(Player).filter(
        Player.position == Position.MID,
        Player.base_rarity != CardRarity.LEGEND,
        ~Player.id.in_(owned_player_ids + [p.id for p in gk_players + def_players])
    ).order_by(func.rand()).limit(4).all()
    
    fwd_players = db.query(Player).filter(
        Player.position == Position.FWD,
        Player.base_rarity != CardRarity.LEGEND,
        ~Player.id.in_(owned_player_ids + [p.id for p in gk_players + def_players + mid_players])
    ).order_by(func.rand()).limit(3).all()

    # 2 suplentes extra aleatorios (de cualquier posición, evitando duplicados, sin leyendas y no poseídos)
    assigned_ids = owned_player_ids + [p.id for p in gk_players + def_players + mid_players + fwd_players]
    extra_players = db.query(Player).filter(
        ~Player.id.in_(assigned_ids),
        Player.base_rarity != CardRarity.LEGEND
    ).order_by(func.rand()).limit(2).all()

    all_players = gk_players + def_players + mid_players + fwd_players + extra_players

    # Crear cartas — los 11 primeros son titulares
    total_ovr = 0
    lineup_count = 0
    assigned_cards = []
    for i, player in enumerate(all_players):
        is_lineup = i < 11  # Primeros 11 = titulares
        card = UserCard(
            user_id=user.id,
            player_id=player.id,
            team_id=team.id,
            league_id=league.id,
            current_overall=player.overall_rating,
            is_in_lineup=is_lineup,
            is_tradeable=True
        )
        db.add(card)
        db.flush()  # para obtener card.id
        assigned_cards.append(AssignedPlayerCard(
            id=card.id,
            player_id=player.id,
            player_name=player.name,
            position=player.position.value if hasattr(player.position, 'value') else str(player.position),
            overall_rating=player.overall_rating,
            base_rarity=player.base_rarity.value if hasattr(player.base_rarity, 'value') else str(player.base_rarity),
            image_url=player.image_url,
            is_in_lineup=is_lineup
        ))
        if is_lineup:
            total_ovr += player.overall_rating
            lineup_count += 1

    # Calcular OVR del equipo
    if lineup_count > 0:
        team.overall_rating = total_ovr / lineup_count

    return team, assigned_cards


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


def _member_to_response(member: LeagueMember, team: Team = None) -> LeagueMemberResponse:
    return LeagueMemberResponse(
        id=member.id,
        user_id=member.user_id,
        username=member.user.username,
        league_points=member.league_points,
        coins=member.coins,
        locked_coins=member.locked_coins,
        is_admin=member.is_admin,
        joined_at=member.joined_at,
        team_name=team.name if team else None,
        team_logo=team.shield_url if team else None
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


@router.post("/invitations/{invitation_id}/accept", response_model=LeagueJoinResponse)
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

    # [↓ SEGURIDAD] Bloqueo pesimista sobre la liga para evitar sobrepasar max_members
    league = db.query(League).filter(League.id == invitation.league_id).with_for_update().first()
    if not league:
         raise HTTPException(status_code=404, detail="Liga no encontrada")

    if league.member_count >= league.max_members:
        raise HTTPException(status_code=400, detail="La liga está llena")

    # [SEGURIDAD] Verificar que el usuario no sea ya miembro (puede haber entrado por código)
    existing_member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league.id,
        LeagueMember.user_id == current_user.id
    ).first()
    if existing_member:
        # Ya es miembro: solo marcar la invitación como aceptada sin crear duplicado
        invitation.status = InvitationStatus.ACCEPTED
        db.commit()
        raise HTTPException(status_code=400, detail="Ya eres miembro de esta liga")

    # Aceptar invitación
    invitation.status = InvitationStatus.ACCEPTED

    # Crear miembro
    member = LeagueMember(
        league_id=league.id,
        user_id=current_user.id
    )
    db.add(member)

    # Auto-crear equipo con 15 jugadores aleatorios
    _, assigned_cards = _create_team_for_league(current_user, league, db)

    db.commit()
    db.refresh(league)

    return LeagueJoinResponse(
        id=league.id,
        name=league.name,
        owner_username=league.owner.username,
        member_count=league.member_count,
        max_members=league.max_members,
        is_public=league.is_public,
        assigned_players=assigned_cards
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


@router.post("/join/{invite_code}", response_model=LeagueJoinResponse)
async def join_by_code(
    invite_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unirse a una liga por código — crea equipo automáticamente"""
    # [↓ SEGURIDAD] Bloqueo pesimista para validar huecos y reparto de jugadores
    league = db.query(League).filter(League.invite_code == invite_code).with_for_update().first()
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
    _, assigned_cards = _create_team_for_league(current_user, league, db)

    db.commit()
    db.refresh(league)

    return LeagueJoinResponse(
        id=league.id,
        name=league.name,
        owner_username=league.owner.username,
        member_count=league.member_count,
        max_members=league.max_members,
        is_public=league.is_public,
        assigned_players=assigned_cards
    )


# ==========================================
# CRUD DE LIGAS
# ==========================================

@router.post("/", response_model=LeagueJoinResponse, status_code=201)
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
    _, assigned_cards = _create_team_for_league(current_user, league, db)

    db.commit()
    db.refresh(league)

    return LeagueJoinResponse(
        id=league.id,
        name=league.name,
        owner_username=league.owner.username,
        member_count=league.member_count,
        max_members=league.max_members,
        is_public=league.is_public,
        assigned_players=assigned_cards
    )


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

    # Obtener equipos de la liga para incluir nombres y logos
    teams = db.query(Team).filter(Team.league_id == league_id).all()
    team_map = {t.user_id: t for t in teams}

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
        members=[_member_to_response(m, team_map.get(m.user_id)) for m in members_sorted]
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
# SALIR DE LIGA / EXPULSAR MIEMBRO
# ==========================================

def _remove_user_from_league(user_id: int, league_id: int, db: Session):
    """Lógica compartida para limpiar un usuario de una liga (salir o ser expulsado)"""
    membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == user_id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=404, detail="El usuario no es miembro de esta liga")

    # 1. Eliminar ofertas del sistema dirigidas al usuario en esta liga
    db.query(SystemOffer).filter(
        SystemOffer.user_id == user_id,
        SystemOffer.league_id == league_id
    ).delete()

    # 2. Devolver pujas del usuario en listados de otros y limpiar pujas en sus propias ventas
    for bid in db.query(ListingBid).join(MarketListing).filter(
        ListingBid.user_id == user_id,
        MarketListing.league_id == league_id
    ).all():
        membership.locked_coins -= bid.amount
        db.delete(bid)

    for lst in db.query(MarketListing).filter(
        MarketListing.seller_id == user_id,
        MarketListing.league_id == league_id
    ).all():
        for bid in db.query(ListingBid).filter(ListingBid.listing_id == lst.id).all():
            bm = db.query(LeagueMember).filter(
                LeagueMember.league_id == league_id,
                LeagueMember.user_id == bid.user_id
            ).first()
            if bm:
                bm.locked_coins -= bid.amount
            db.delete(bid)
        db.delete(lst)

    # 3. Eliminar equipo asociado y sus alineaciones (FK constraint)
    team = db.query(Team).filter(
        Team.user_id == user_id,
        Team.league_id == league_id
    ).first()
    
    if team:
        # Primero eliminar alineaciones que referencian a este equipo
        lineup_ids = [l.id for l in db.query(GameweekLineup).filter(GameweekLineup.team_id == team.id).all()]
        if lineup_ids:
            # Eliminar jugadores de las alineaciones (hijos) antes que las alineaciones (padres)
            db.query(GameweekLineupPlayer).filter(GameweekLineupPlayer.lineup_id.in_(lineup_ids)).delete(synchronize_session=False)
            db.query(GameweekLineup).filter(GameweekLineup.id.in_(lineup_ids)).delete(synchronize_session=False)
        
        # Eliminar historial de batallas en Arena
        db.query(ArenaBattle).filter(
            (ArenaBattle.team1_id == team.id) | (ArenaBattle.team2_id == team.id)
        ).delete(synchronize_session=False)
        
        db.delete(team)

    # 4. Limpiar trazabilidad de sobres (PackOpeningCard) antes de borrar PackOpening o UserCard
    pack_opening_ids = [p.id for p in db.query(PackOpening).filter(
        PackOpening.user_id == user_id,
        PackOpening.league_id == league_id
    ).all()]
    if pack_opening_ids:
        db.query(PackOpeningCard).filter(PackOpeningCard.pack_opening_id.in_(pack_opening_ids)).delete(synchronize_session=False)
        db.query(PackOpening).filter(PackOpening.id.in_(pack_opening_ids)).delete(synchronize_session=False)

    # 5. Eliminar TODAS las cartas del usuario que pertenecen a esta liga
    # Ya sea que estuvieran en el equipo o en el inventario/mercado
    db.query(UserCard).filter(
        UserCard.user_id == user_id,
        UserCard.league_id == league_id
    ).delete()

    # 6. Eliminar la membresía
    db.delete(membership)
    # Se omite el commit interno para mantener atomicidad en las llamadas padre


def _delete_league_completely(league: League, db: Session):
    """Elimina una liga completamente junto con todos sus datos asociados."""
    league_id = league.id
    
    # 1. SystemOffers
    db.query(SystemOffer).filter(SystemOffer.league_id == league_id).delete()

    # 2. Pujas de mercado entre usuarios (antes de borrar listados)
    for bid in db.query(ListingBid).join(MarketListing).filter(
        MarketListing.league_id == league_id
    ).all():
        m = db.query(LeagueMember).filter(
            LeagueMember.league_id == league_id,
            LeagueMember.user_id == bid.user_id
        ).first()
        if m:
            m.locked_coins -= bid.amount
        db.delete(bid)

    db.query(MarketListing).filter(MarketListing.league_id == league_id).delete()
    
    # 3. Auctions
    auctions = db.query(MarketAuction).filter(MarketAuction.league_id == league_id).all()
    for auction in auctions:
        slot_ids = [s.id for s in db.query(AuctionSlot).filter(AuctionSlot.auction_id == auction.id).all()]
        if slot_ids:
            db.query(AuctionBid).filter(AuctionBid.slot_id.in_(slot_ids)).delete(synchronize_session=False)
            db.query(AuctionSlot).filter(AuctionSlot.auction_id == auction.id).delete()
        db.delete(auction)
        
    # Eliminar pujas directas del usuario en subastas si quedase alguna (trazabilidad)
    db.query(AuctionBid).filter(AuctionBid.user_id.in_(
        db.query(LeagueMember.user_id).filter(LeagueMember.league_id == league_id)
    )).delete(synchronize_session=False)        
    # 4. Pack Openings
    po_ids = [p.id for p in db.query(PackOpening).filter(PackOpening.league_id == league_id).all()]
    if po_ids:
        db.query(PackOpeningCard).filter(PackOpeningCard.pack_opening_id.in_(po_ids)).delete(synchronize_session=False)
        db.query(PackOpening).filter(PackOpening.id.in_(po_ids)).delete(synchronize_session=False)
    
    # 5. GameweekLineups
    team_ids = [t.id for t in db.query(Team).filter(Team.league_id == league_id).all()]
    if team_ids:
        # Eliminar jugadores de las alineaciones (hijos) antes que las alineaciones (padres)
        db.query(GameweekLineupPlayer).filter(GameweekLineupPlayer.lineup_id.in_(
            db.query(GameweekLineup.id).filter(GameweekLineup.team_id.in_(team_ids))
        )).delete(synchronize_session=False)
        db.query(GameweekLineup).filter(GameweekLineup.team_id.in_(team_ids)).delete(synchronize_session=False)
        
    # 6. UserCards (eliminar las cartas procedentes de la liga para limpiar BD)
    db.query(UserCard).filter(UserCard.league_id == league_id).delete()
    
    # 7. Arena Battles (referencian teams via FK — limpiar antes de borrar teams)
    if team_ids:
        db.query(ArenaBattle).filter(
            (ArenaBattle.team1_id.in_(team_ids)) | (ArenaBattle.team2_id.in_(team_ids))
        ).delete(synchronize_session=False)
    
    # 8. Teams
    db.query(Team).filter(Team.league_id == league_id).delete()
    
    # 9. Notifications (referencian league via FK)
    db.query(Notification).filter(Notification.league_id == league_id).delete()
    
    # 10. League (cascade borra members e invitations)
    db.delete(league)
    db.commit()


@router.delete("/{league_id}/leave")
async def leave_league(
    league_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Salir de una liga (voluntario)"""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="Liga no encontrada")

    # Contar miembros
    member_count = db.query(func.count(LeagueMember.id)).filter(LeagueMember.league_id == league_id).scalar()

    if member_count <= 1:
        # Es el último miembro, eliminar la liga por completo
        _delete_league_completely(league, db)
        return {"message": "Has salido de la liga y, al quedar vacía, ha sido eliminada."}

    if league.owner_id == current_user.id:
        # El que sale es el dueño. Traspasar poderes.
        new_owner = db.query(LeagueMember).filter(
            LeagueMember.league_id == league_id,
            LeagueMember.user_id != current_user.id
        ).order_by(LeagueMember.is_admin.desc(), LeagueMember.joined_at.asc()).first()
        
        if new_owner:
            league.owner_id = new_owner.user_id
            new_owner.is_admin = True
            db.commit()

    # Si llegamos aquí, eliminamos al usuario normalmente
    _remove_user_from_league(current_user.id, league_id, db)
    db.commit()
    
    return {"message": "Has salido de la liga exitosamente"}


@router.delete("/{league_id}/kick/{target_user_id}")
async def kick_member(
    league_id: int,
    target_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Expulsar a un usuario de la liga (Solo Admin/Owner)"""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="Liga no encontrada")

    # Verificar permisos de quien ejecuta la acción
    current_membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()

    if not current_membership or not current_membership.is_admin:
        if league.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permisos para expulsar jugadores")

    # Verificar a quién se expulsa
    if target_user_id == league.owner_id:
        raise HTTPException(status_code=400, detail="No puedes expulsar al creador de la liga")
        
    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes expulsarte a ti mismo, usa la opción Salir")

    _remove_user_from_league(target_user_id, league_id, db)
    db.commit()
    
    return {"message": "Jugador expulsado de la liga"}
