from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, aliased
from sqlalchemy import and_, or_, func, desc, not_
from typing import List, Optional
import re

from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.models import Team, TeamStatistics, Match

router = APIRouter()


def is_professional_team(team_name: str) -> bool:
    """
    Verifica se um time é profissional (masculino, categoria principal).

    Retorna False para:
    - Times femininos (W, Women, Feminino, etc)
    - Times de base (U20, U19, U17, Sub-20, etc)
    - Times reservas (B, Reserve, II, etc)
    """
    if not team_name:
        return True

    name_lower = team_name.lower()

    # Padrões que indicam times NÃO profissionais
    non_professional_patterns = [
        r'\bu\d{1,2}\b',           # U20, U19, U17, U21, U23
        r'\bu-\d{1,2}\b',          # U-20, U-19
        r'\bunder\s*\d{1,2}\b',    # Under 20, Under19
        r'\bsub\s*-?\d{1,2}\b',    # Sub 20, Sub-20, Sub20
        r'\bw\b',                   # W (women)
        r'\bwomen\b',               # Women
        r'\bfeminino\b',            # Feminino
        r'\bfeminina\b',            # Feminina
        r'\breserve\b',             # Reserve
        r'\breservas\b',            # Reservas
        r'\s+b\b',                  # Team B (com espaço antes)
        r'\s+ii\b',                 # Team II
        r'\bjuvenil\b',             # Juvenil
        r'\byouth\b',               # Youth
    ]

    for pattern in non_professional_patterns:
        if re.search(pattern, name_lower):
            return False

    return True


def get_professional_teams_filter():
    """
    Retorna um filtro SQLAlchemy que exclui times não profissionais.
    """
    # Lista de padrões SQL LIKE para exclusão
    patterns = [
        '%U20%', '%U-20%', '%U 20%', '%Under 20%', '%Sub 20%', '%Sub-20%',
        '%U19%', '%U-19%', '%U 19%', '%Under 19%', '%Sub 19%', '%Sub-19%',
        '%U17%', '%U-17%', '%U 17%', '%Under 17%', '%Sub 17%', '%Sub-17%',
        '%U21%', '%U-21%', '%U 21%', '%Under 21%', '%Sub 21%', '%Sub-21%',
        '%U23%', '%U-23%', '%U 23%', '%Under 23%', '%Sub 23%', '%Sub-23%',
        '% W %', '%Women%', '%Feminino%', '%Feminina%',
        '%Reserve%', '%Reservas%', '% B', '% II',
        '%Juvenil%', '%Youth%'
    ]

    # Criar filtro NOT LIKE para cada padrão
    filters = [not_(Team.name.ilike(pattern)) for pattern in patterns]

    return and_(*filters)


@router.get("/search")
@limiter.limit("60/minute")
async def search_teams(
    request: Request,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=2, description="Nome do time para buscar"),
    limit: int = 20
):
    """
    🔍 BUSCAR TIMES

    Busca times no DB por nome (mínimo 2 caracteres)
    Filtra automaticamente times U20, femininos e reservas

    Rate limit: 60/min
    """
    # Buscar times que contenham o termo + filtro de times profissionais
    teams = db.query(Team).filter(
        and_(
            Team.name.ilike(f'%{q}%'),
            get_professional_teams_filter()
        )
    ).limit(limit).all()

    results = []
    for team in teams:
        # Contar jogos do time
        total_matches = db.query(Match).filter(
            or_(
                Match.home_team_id == team.id,
                Match.away_team_id == team.id
            )
        ).count()

        results.append({
            'id': team.id,
            'name': team.name,
            'api_team_id': team.api_team_id if hasattr(team, 'api_team_id') else team.external_id,
            'logo_url': team.logo_url,
            'total_matches': total_matches
        })

    return {
        'success': True,
        'total': len(results),
        'teams': results
    }


@router.get("/")
async def get_teams(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    league: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None
):
    """Get teams with optional filters (only professional teams)"""
    query = db.query(Team).filter(
        and_(
            Team.is_active == True,
            get_professional_teams_filter()
        )
    )

    if league:
        query = query.filter(Team.league == league)
    if country:
        query = query.filter(Team.country == country)
    if search:
        query = query.filter(Team.name.ilike(f"%{search}%"))

    teams = query.offset(skip).limit(limit).all()

    return {
        "teams": [
            {
                "id": team.id,
                "external_id": team.external_id,
                "name": team.name,
                "short_name": team.short_name,
                "country": team.country,
                "league": team.league,
                "founded": team.founded,
                "venue": team.venue,
                "logo_url": team.logo_url,
                "elo_rating": team.elo_rating,
                "form_rating": team.form_rating,
                "attack_rating": team.attack_rating,
                "defense_rating": team.defense_rating
            }
            for team in teams
        ],
        "count": len(teams)
    }

@router.get("/{team_id}")
async def get_team_details(team_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a team"""
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get latest statistics
    latest_stats = db.query(TeamStatistics).filter(
        TeamStatistics.team_id == team_id
    ).order_by(TeamStatistics.last_updated.desc()).first()

    return {
        "id": team.id,
        "external_id": team.external_id,
        "name": team.name,
        "short_name": team.short_name,
        "country": team.country,
        "league": team.league,
        "founded": team.founded,
        "venue": team.venue,
        "logo_url": team.logo_url,
        "ratings": {
            "elo_rating": team.elo_rating,
            "form_rating": team.form_rating,
            "attack_rating": team.attack_rating,
            "defense_rating": team.defense_rating
        },
        "season_stats": {
            "season": latest_stats.season,
            "games_played": latest_stats.games_played,
            "wins": latest_stats.wins,
            "draws": latest_stats.draws,
            "losses": latest_stats.losses,
            "goals_for": latest_stats.goals_for,
            "goals_against": latest_stats.goals_against,
            "clean_sheets": latest_stats.clean_sheets,
            "win_rate": latest_stats.wins / latest_stats.games_played if latest_stats.games_played > 0 else 0,
            "points": latest_stats.wins * 3 + latest_stats.draws,
            "points_per_game": (latest_stats.wins * 3 + latest_stats.draws) / latest_stats.games_played if latest_stats.games_played > 0 else 0
        } if latest_stats else None,
        "advanced_metrics": {
            "avg_xg_for": latest_stats.avg_xg_for,
            "avg_xg_against": latest_stats.avg_xg_against,
            "avg_possession": latest_stats.avg_possession,
            "avg_shots_for": latest_stats.avg_shots_for,
            "avg_shots_against": latest_stats.avg_shots_against,
            "avg_corners_for": latest_stats.avg_corners_for,
            "avg_corners_against": latest_stats.avg_corners_against
        } if latest_stats else None,
        "home_away_split": {
            "home_record": f"{latest_stats.home_wins}-{latest_stats.home_draws}-{latest_stats.home_losses}",
            "away_record": f"{latest_stats.away_wins}-{latest_stats.away_draws}-{latest_stats.away_losses}",
            "home_win_rate": latest_stats.home_wins / (latest_stats.home_wins + latest_stats.home_draws + latest_stats.home_losses) if (latest_stats.home_wins + latest_stats.home_draws + latest_stats.home_losses) > 0 else 0,
            "away_win_rate": latest_stats.away_wins / (latest_stats.away_wins + latest_stats.away_draws + latest_stats.away_losses) if (latest_stats.away_wins + latest_stats.away_draws + latest_stats.away_losses) > 0 else 0
        } if latest_stats else None
    }

@router.get("/{team_id}/statistics")
async def get_team_statistics(
    team_id: int,
    db: Session = Depends(get_db),
    season: Optional[str] = None
):
    """Get team statistics for a specific season"""
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    query = db.query(TeamStatistics).filter(TeamStatistics.team_id == team_id)

    if season:
        query = query.filter(TeamStatistics.season == season)

    stats = query.order_by(TeamStatistics.last_updated.desc()).all()

    return {
        "team_id": team_id,
        "team_name": team.name,
        "statistics": [
            {
                "season": stat.season,
                "games_played": stat.games_played,
                "wins": stat.wins,
                "draws": stat.draws,
                "losses": stat.losses,
                "goals_for": stat.goals_for,
                "goals_against": stat.goals_against,
                "goal_difference": stat.goals_for - stat.goals_against,
                "clean_sheets": stat.clean_sheets,
                "points": stat.wins * 3 + stat.draws,
                "avg_xg_for": stat.avg_xg_for,
                "avg_xg_against": stat.avg_xg_against,
                "avg_possession": stat.avg_possession,
                "home_record": {
                    "wins": stat.home_wins,
                    "draws": stat.home_draws,
                    "losses": stat.home_losses
                },
                "away_record": {
                    "wins": stat.away_wins,
                    "draws": stat.away_draws,
                    "losses": stat.away_losses
                },
                "last_updated": stat.last_updated
            }
            for stat in stats
        ]
    }

@router.get("/{team_id}/recent-matches")
async def get_team_recent_matches(
    team_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=30)
):
    """Get recent matches for a team"""
    from app.models import Match

    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    recent_matches = db.query(Match).filter(
        (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
    ).order_by(Match.match_date.desc()).limit(limit).all()

    return {
        "team_id": team_id,
        "team_name": team.name,
        "recent_matches": [
            {
                "id": match.id,
                "date": match.match_date,
                "home_team": match.home_team.name,
                "away_team": match.away_team.name,
                "score": f"{match.home_score}-{match.away_score}" if match.home_score is not None else "TBD",
                "status": match.status,
                "league": match.league,
                "venue": match.venue,
                "is_home": match.home_team_id == team_id,
                "result": _get_team_result(match, team_id) if match.status == "FINISHED" else None
            }
            for match in recent_matches
        ]
    }

@router.get("/leagues")
async def get_leagues(db: Session = Depends(get_db)):
    """Get list of available leagues"""
    leagues = db.query(Team.league).filter(
        Team.league.isnot(None),
        Team.is_active == True
    ).distinct().all()

    return {
        "leagues": [league[0] for league in leagues if league[0]]
    }

@router.get("/countries")
async def get_countries(db: Session = Depends(get_db)):
    """Get list of available countries"""
    countries = db.query(Team.country).filter(
        Team.country.isnot(None),
        Team.is_active == True
    ).distinct().all()

    return {
        "countries": [country[0] for country in countries if country[0]]
    }

def _get_team_result(match, team_id: int) -> str:
    """Get result from team's perspective (W/D/L)"""
    if match.home_score is None or match.away_score is None:
        return None

    is_home = match.home_team_id == team_id
    team_score = match.home_score if is_home else match.away_score
    opponent_score = match.away_score if is_home else match.home_score

    if team_score > opponent_score:
        return "W"
    elif team_score == opponent_score:
        return "D"
    else:
        return "L"


@router.get("/{team_id}/history")
@limiter.limit("60/minute")
async def get_team_history(
    request: Request,
    team_id: int,
    db: Session = Depends(get_db),
    venue: Optional[str] = Query(None, description="home, away, ou all"),
    limit: int = Query(10, description="Número de jogos (padrão 10)"),
    league_id: Optional[int] = None
):
    """
    📊 HISTÓRICO DO TIME

    Retorna últimos N jogos do time com filtros:
    - venue: 'home' (casa), 'away' (fora), ou 'all' (todos)
    - limit: número de jogos (padrão 10)
    - league_id: filtrar por liga específica

    Filtra automaticamente adversários U20, femininos e reservas

    Rate limit: 60/min
    """
    # Verificar se time existe e é profissional
    team = db.query(Team).filter(
        and_(
            Team.id == team_id,
            get_professional_teams_filter()
        )
    ).first()

    if not team:
        return {
            'success': False,
            'error': 'Time não encontrado ou não é um time profissional',
            'matches': []
        }

    # 🔧 CORRIGIDO: Usar subquery ao invés de JOIN duplo
    # Cria subquery para pegar IDs de times profissionais
    professional_teams_subquery = db.query(Team.id).filter(
        get_professional_teams_filter()
    ).subquery()

    # Query base - jogos FINALIZADOS apenas
    query = db.query(Match).filter(
        and_(
            or_(
                Match.home_team_id == team_id,
                Match.away_team_id == team_id
            ),
            Match.status == 'FT',  # Apenas jogos finalizados
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
            # 🔧 Garante que AMBOS os times sejam profissionais
            Match.home_team_id.in_(professional_teams_subquery),
            Match.away_team_id.in_(professional_teams_subquery)
        )
    )

    # Filtro de venue (casa/fora)
    if venue == 'home':
        query = query.filter(Match.home_team_id == team_id)
    elif venue == 'away':
        query = query.filter(Match.away_team_id == team_id)

    # Filtro de liga
    if league_id:
        query = query.filter(Match.league_id == league_id)

    # Ordenar por data (mais recentes primeiro) e limitar
    matches = query.order_by(Match.match_date.desc()).limit(limit).all()

    results = []

    for match in matches:
        is_home = match.home_team_id == team_id

        # Determinar resultado para o time
        if is_home:
            if match.home_score > match.away_score:
                result = 'W'  # Vitória
            elif match.home_score < match.away_score:
                result = 'L'  # Derrota
            else:
                result = 'D'  # Empate
        else:
            if match.away_score > match.home_score:
                result = 'W'
            elif match.away_score < match.home_score:
                result = 'L'
            else:
                result = 'D'

        results.append({
            'id': match.id,
            'match_date': match.match_date.isoformat() if match.match_date else None,
            'home_team': {
                'id': match.home_team.id,
                'name': match.home_team.name,
                'logo': match.home_team.logo_url
            } if match.home_team else None,
            'away_team': {
                'id': match.away_team.id,
                'name': match.away_team.name,
                'logo': match.away_team.logo_url
            } if match.away_team else None,
            'home_score': match.home_score,
            'away_score': match.away_score,
            'venue': 'home' if is_home else 'away',
            'result': result,  # W, L, D
            'league': {
                'id': None,
                'name': match.league if match.league else 'Unknown'
            }
        })

    return {
        'success': True,
        'team': {
            'id': team.id,
            'name': team.name,
            'logo': team.logo_url
        },
        'total': len(results),
        'matches': results
    }


@router.get("/{team_id}/stats")
@limiter.limit("60/minute")
async def get_team_stats(
    request: Request,
    team_id: int,
    db: Session = Depends(get_db),
    last_n_games: int = Query(10, description="Últimos N jogos para calcular estatísticas")
):
    """
    📈 ESTATÍSTICAS DO TIME

    Retorna estatísticas completas:
    - Forma recente (últimos N jogos)
    - Vitórias/Empates/Derrotas (geral, casa, fora)
    - Média de gols (marcados e sofridos)
    - Sequência atual (W/L/D)
    - Performance em casa vs fora

    Rate limit: 60/min
    """
    # Verificar se time existe
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        return {
            'success': False,
            'error': 'Time não encontrado'
        }

    # Buscar jogos finalizados do time
    all_matches = db.query(Match).filter(
        and_(
            or_(
                Match.home_team_id == team_id,
                Match.away_team_id == team_id
            ),
            Match.status == 'FT',
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        )
    ).order_by(Match.match_date.desc()).all()

    if not all_matches:
        return {
            'success': True,
            'team': {
                'id': team.id,
                'name': team.name,
                'logo': team.logo_url
            },
            'stats': None,
            'message': 'Nenhum jogo finalizado encontrado'
        }

    # Limitar aos últimos N jogos
    recent_matches = all_matches[:last_n_games]

    # Calcular estatísticas gerais
    stats_general = {'W': 0, 'D': 0, 'L': 0, 'goals_scored': 0, 'goals_conceded': 0}
    stats_home = {'W': 0, 'D': 0, 'L': 0, 'goals_scored': 0, 'goals_conceded': 0}
    stats_away = {'W': 0, 'D': 0, 'L': 0, 'goals_scored': 0, 'goals_conceded': 0}

    form = []  # Últimos 5 jogos

    for idx, match in enumerate(recent_matches):
        is_home = match.home_team_id == team_id

        if is_home:
            goals_scored = match.home_score
            goals_conceded = match.away_score
        else:
            goals_scored = match.away_score
            goals_conceded = match.home_score

        # Determinar resultado
        if goals_scored > goals_conceded:
            result = 'W'
        elif goals_scored < goals_conceded:
            result = 'L'
        else:
            result = 'D'

        # Estatísticas gerais
        stats_general[result] += 1
        stats_general['goals_scored'] += goals_scored
        stats_general['goals_conceded'] += goals_conceded

        # Estatísticas casa/fora
        if is_home:
            stats_home[result] += 1
            stats_home['goals_scored'] += goals_scored
            stats_home['goals_conceded'] += goals_conceded
        else:
            stats_away[result] += 1
            stats_away['goals_scored'] += goals_scored
            stats_away['goals_conceded'] += goals_conceded

        # Forma recente (últimos 5)
        if idx < 5:
            form.append(result)

    # Calcular médias
    total_games = len(recent_matches)
    avg_goals_scored = stats_general['goals_scored'] / total_games if total_games > 0 else 0
    avg_goals_conceded = stats_general['goals_conceded'] / total_games if total_games > 0 else 0

    # Calcular win rate
    win_rate = (stats_general['W'] / total_games * 100) if total_games > 0 else 0

    # Sequência atual
    current_streak = 0
    streak_type = form[0] if form else None

    for f in form:
        if f == streak_type:
            current_streak += 1
        else:
            break

    return {
        'success': True,
        'team': {
            'id': team.id,
            'name': team.name,
            'logo': team.logo_url
        },
        'period': f'Últimos {total_games} jogos',
        'stats': {
            'general': {
                'played': total_games,
                'wins': stats_general['W'],
                'draws': stats_general['D'],
                'losses': stats_general['L'],
                'win_rate': round(win_rate, 1),
                'goals_scored': stats_general['goals_scored'],
                'goals_conceded': stats_general['goals_conceded'],
                'goal_difference': stats_general['goals_scored'] - stats_general['goals_conceded'],
                'avg_goals_scored': round(avg_goals_scored, 2),
                'avg_goals_conceded': round(avg_goals_conceded, 2)
            },
            'home': {
                'played': stats_home['W'] + stats_home['D'] + stats_home['L'],
                'wins': stats_home['W'],
                'draws': stats_home['D'],
                'losses': stats_home['L'],
                'goals_scored': stats_home['goals_scored'],
                'goals_conceded': stats_home['goals_conceded']
            },
            'away': {
                'played': stats_away['W'] + stats_away['D'] + stats_away['L'],
                'wins': stats_away['W'],
                'draws': stats_away['D'],
                'losses': stats_away['L'],
                'goals_scored': stats_away['goals_scored'],
                'goals_conceded': stats_away['goals_conceded']
            },
            'form': {
                'recent_5': form[:5],  # W, L, D, W, W
                'current_streak': {
                    'type': streak_type,  # W, L, ou D
                    'count': current_streak
                }
            }
        }
    }


@router.get("/{team_id}/head-to-head/{opponent_id}")
@limiter.limit("60/minute")
async def get_head_to_head(
    request: Request,
    team_id: int,
    opponent_id: int,
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    🆚 CONFRONTO DIRETO (HEAD-TO-HEAD)

    Retorna histórico de confrontos diretos entre dois times

    Rate limit: 60/min
    """
    # Verificar se times existem
    team1 = db.query(Team).filter(Team.id == team_id).first()
    team2 = db.query(Team).filter(Team.id == opponent_id).first()

    if not team1 or not team2:
        return {
            'success': False,
            'error': 'Time não encontrado'
        }

    # Buscar confrontos diretos
    h2h_matches = db.query(Match).filter(
        and_(
            Match.status == 'FT',
            or_(
                and_(
                    Match.home_team_id == team_id,
                    Match.away_team_id == opponent_id
                ),
                and_(
                    Match.home_team_id == opponent_id,
                    Match.away_team_id == team_id
                )
            )
        )
    ).order_by(Match.match_date.desc()).limit(limit).all()

    results = []
    team1_wins = 0
    team2_wins = 0
    draws = 0

    for match in h2h_matches:
        if match.home_score > match.away_score:
            winner = match.home_team_id
        elif match.home_score < match.away_score:
            winner = match.away_team_id
        else:
            winner = None

        if winner == team_id:
            team1_wins += 1
        elif winner == opponent_id:
            team2_wins += 1
        else:
            draws += 1

        results.append({
            'id': match.id,
            'match_date': match.match_date.isoformat() if match.match_date else None,
            'home_team': {
                'id': match.home_team.id,
                'name': match.home_team.name,
                'logo': match.home_team.logo_url
            },
            'away_team': {
                'id': match.away_team.id,
                'name': match.away_team.name,
                'logo': match.away_team.logo_url
            },
            'home_score': match.home_score,
            'away_score': match.away_score,
            'winner_id': winner
        })

    return {
        'success': True,
        'team1': {
            'id': team1.id,
            'name': team1.name,
            'logo': team1.logo_url
        },
        'team2': {
            'id': team2.id,
            'name': team2.name,
            'logo': team2.logo_url
        },
        'summary': {
            'total_matches': len(results),
            'team1_wins': team1_wins,
            'team2_wins': team2_wins,
            'draws': draws
        },
        'matches': results
    }