#!/usr/bin/env python3
"""
📰 News & Injuries Endpoint
Fornece notícias de futebol através de RSS feeds e API-Sports
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from datetime import datetime, timedelta
import feedparser
from pydantic import BaseModel

from app.core.database import get_db
from app.models.match import Match
from app.models.team import Team
from app.services.api_football_service import APIFootballService

router = APIRouter()
api_football = APIFootballService()

# Pydantic models
class NewsSource(BaseModel):
    id: str
    name: str

class NewsItem(BaseModel):
    id: str
    title: str
    description: str
    url: str
    source: NewsSource
    author: Optional[str] = None
    publishedAt: str
    urlToImage: Optional[str] = None
    category: str = "sports"
    language: str = "pt"

class NewsResponse(BaseModel):
    success: bool
    items: List[NewsItem]
    total: int
    sources: List[str]

class InjuryStatus(BaseModel):
    id: int
    player_name: str
    team_name: str
    team_id: int
    position: Optional[str] = None
    injury_type: str
    severity: str
    status: str  # injured, recovering, fit
    description: str
    expected_return: Optional[str] = None
    reported_at: str

class InjuryResponse(BaseModel):
    success: bool
    injuries: List[InjuryStatus]
    total: int

# RSS Feeds por liga - URLs TESTADOS E FUNCIONAIS
RSS_FEEDS = {
    'brasileirao': [
        {
            'name': 'ESPN Brasil',
            'url': 'https://www.espn.com.br/espn/rss/news',
            'language': 'pt'
        },
        {
            'name': 'Lance!',
            'url': 'https://www.lance.com.br/feed',
            'language': 'pt'
        }
    ],
    'libertadores': [
        {
            'name': 'ESPN',
            'url': 'https://www.espn.com.br/espn/rss/news',
            'language': 'pt'
        }
    ],
    'premier-league': [
        {
            'name': 'BBC Sport',
            'url': 'https://feeds.bbci.co.uk/sport/football/rss.xml',
            'language': 'en'
        },
        {
            'name': 'Sky Sports',
            'url': 'https://www.skysports.com/rss/12040',
            'language': 'en'
        }
    ],
    'la-liga': [
        {
            'name': 'ESPN',
            'url': 'https://www.espn.com/espn/rss/news',
            'language': 'en'
        }
    ],
    'all': [
        {
            'name': 'ESPN Brasil',
            'url': 'https://www.espn.com.br/espn/rss/news',
            'language': 'pt'
        },
        {
            'name': 'BBC Sport',
            'url': 'https://feeds.bbci.co.uk/sport/football/rss.xml',
            'language': 'en'
        },
        {
            'name': 'Sky Sports Football',
            'url': 'https://www.skysports.com/rss/12040',
            'language': 'en'
        }
    ]
}

def parse_rss_feed(feed_url: str, feed_name: str, language: str = 'pt') -> List[NewsItem]:
    """Parse RSS feed e retorna lista de NewsItem"""
    try:
        print(f"[RSS] Fetching feed: {feed_name} - {feed_url}")
        feed = feedparser.parse(feed_url)

        if not feed.entries:
            print(f"[RSS] No entries found in feed: {feed_name}")
            return []

        print(f"[RSS] Found {len(feed.entries)} entries in {feed_name}")
        news_items = []

        for entry in feed.entries[:20]:  # Limitar a 20 itens por feed
            # Extrair imagem se disponível
            image_url = None
            if hasattr(entry, 'media_content') and entry.media_content:
                image_url = entry.media_content[0].get('url')
            elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                image_url = entry.media_thumbnail[0].get('url')
            elif hasattr(entry, 'enclosures') and entry.enclosures:
                image_url = entry.enclosures[0].get('href')

            # Formatar data
            pub_date = entry.get('published', entry.get('updated', datetime.now().isoformat()))

            news_item = NewsItem(
                id=entry.get('id', entry.get('link', f"{feed_name}_{len(news_items)}")),
                title=entry.get('title', 'Sem título'),
                description=entry.get('summary', entry.get('description', entry.get('title', ''))),
                url=entry.get('link', ''),
                source=NewsSource(id=feed_name.lower().replace(' ', '_'), name=feed_name),
                author=entry.get('author', feed_name),
                publishedAt=pub_date,
                urlToImage=image_url,
                category='sports',
                language=language
            )
            news_items.append(news_item)

        print(f"[RSS] Successfully parsed {len(news_items)} items from {feed_name}")
        return news_items
    except Exception as e:
        print(f"[RSS] Error parsing RSS feed {feed_url}: {e}")
        import traceback
        traceback.print_exc()
        return []

@router.get("/rss", response_model=NewsResponse)
async def get_news_from_rss(
    league: str = Query('all', description="Liga para buscar notícias"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Busca notícias de RSS feeds

    **Ligas disponíveis:**
    - all: Todas as notícias
    - brasileirao: Brasileirão Série A
    - libertadores: Copa Libertadores
    - premier-league: Premier League
    - la-liga: La Liga
    """
    feeds_to_parse = RSS_FEEDS.get(league, RSS_FEEDS['all'])

    all_news = []
    sources_used = []

    for feed_config in feeds_to_parse:
        news_items = parse_rss_feed(
            feed_config['url'],
            feed_config['name'],
            feed_config['language']
        )
        all_news.extend(news_items)
        if news_items:
            sources_used.append(feed_config['name'])

    # Ordenar por data de publicação (mais recentes primeiro)
    all_news.sort(key=lambda x: x.publishedAt, reverse=True)

    # Limitar resultados
    all_news = all_news[:limit]

    return NewsResponse(
        success=True,
        items=all_news,
        total=len(all_news),
        sources=sources_used
    )

@router.get("/official", response_model=NewsResponse)
async def get_official_news(
    league: str = Query('brasileirao', description="Liga para buscar notícias oficiais")
):
    """
    Busca notícias de fontes oficiais (RSS feeds oficiais)
    """
    return await get_news_from_rss(league=league, limit=30)

@router.get("/injuries", response_model=InjuryResponse)
async def get_injuries(
    league: Optional[str] = Query(None, description="Filtrar por liga"),
    team_id: Optional[int] = Query(None, description="Filtrar por time (API-Sports team ID)"),
    status: Optional[str] = Query(None, description="Status: injured, recovering, fit"),
    season: int = Query(2025, description="Temporada (ano)"),
    db: Session = Depends(get_db)
):
    """
    📋 Retorna lesões de jogadores via API-Sports

    Ligas suportadas (com seus IDs):
    - brasileirao: Brasileirão Série A (71)
    - premier-league: Premier League (39)
    - la-liga: La Liga (140)
    - bundesliga: Bundesliga (78)
    - serie-a: Serie A Itália (135)
    - ligue-1: Ligue 1 (61)
    - libertadores: Copa Libertadores (13)
    - champions-league: UEFA Champions League (2)
    """
    # Mapeamento de ligas para IDs da API-Sports
    league_ids = {
        'brasileirao': 71,
        'brasileirao-a': 71,
        'premier-league': 39,
        'la-liga': 140,
        'bundesliga': 78,
        'serie-a': 135,
        'ligue-1': 61,
        'libertadores': 13,
        'champions-league': 2,
        'europa-league': 3,
        'copa-do-brasil': 73,
    }

    # Determinar league_id
    league_id = None
    if league:
        league_id = league_ids.get(league.lower())
        if not league_id:
            raise HTTPException(status_code=400, detail=f"Liga '{league}' não suportada. Use: {list(league_ids.keys())}")

    try:
        # Buscar injuries via API-Sports
        injuries_data = await api_football.get_injuries(
            league_id=league_id,
            season=season,
            team_id=team_id
        )

        # Processar e formatar injuries
        processed_injuries = []
        for idx, injury in enumerate(injuries_data):
            player = injury.get('player', {})
            team = injury.get('team', {})
            fixture = injury.get('fixture', {})

            # Extrair informações da lesão
            injury_type = player.get('reason', 'Unknown')

            # Determinar severidade baseado no tipo
            severity = 'medium'
            if any(word in injury_type.lower() for word in ['fracture', 'rupture', 'torn']):
                severity = 'high'
            elif any(word in injury_type.lower() for word in ['minor', 'knock', 'bruise']):
                severity = 'low'

            # Determinar status
            injury_status = 'injured'  # Default

            # Filtrar por status se especificado
            if status and injury_status != status:
                continue

            processed_injuries.append(InjuryStatus(
                id=idx + 1,
                player_name=player.get('name', 'Unknown Player'),
                team_name=team.get('name', 'Unknown Team'),
                team_id=team.get('id', 0),
                position=player.get('type', None),  # Posição (ex: Defender, Forward)
                injury_type=injury_type,
                severity=severity,
                status=injury_status,
                description=f"{player.get('name', 'Player')} - {injury_type}",
                expected_return=None,  # API-Sports não fornece data de retorno
                reported_at=datetime.now().isoformat()
            ))

        return InjuryResponse(
            success=True,
            injuries=processed_injuries,
            total=len(processed_injuries)
        )

    except Exception as e:
        # Log error mas retorna lista vazia ao invés de falhar
        print(f"Erro ao buscar lesões: {e}")
        return InjuryResponse(
            success=False,
            injuries=[],
            total=0
        )

@router.get("/upcoming-matches-news")
async def get_upcoming_matches_news(
    days_ahead: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Retorna notícias contextualizadas com próximos jogos
    Útil para NewsInjuries page - combina próximos jogos com notícias relevantes
    """
    # Buscar próximos jogos
    now = datetime.now()
    future_date = now + timedelta(days=days_ahead)

    matches = db.query(Match).filter(
        and_(
            Match.match_date >= now,
            Match.match_date <= future_date,
            Match.status.in_(['NS', 'TBD', 'SCHEDULED'])
        )
    ).order_by(Match.match_date).limit(limit).all()

    matches_data = []
    for match in matches:
        home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == match.away_team_id).first()

        matches_data.append({
            'match_id': match.id,
            'match_date': match.match_date.isoformat(),
            'home_team': home_team.name if home_team else 'Unknown',
            'away_team': away_team.name if away_team else 'Unknown',
            'league': match.league,
            'venue': match.venue,
            'news_keywords': [
                home_team.name if home_team else '',
                away_team.name if away_team else '',
                match.league
            ]
        })

    return {
        'success': True,
        'matches': matches_data,
        'total': len(matches_data),
        'message': 'Use os keywords para buscar notícias relevantes via /news/rss'
    }

@router.get("/search")
async def search_news(
    query: str = Query(..., description="Termo de busca"),
    language: str = Query('pt', description="Idioma: pt, en, es"),
    limit: int = Query(20, ge=1, le=50)
):
    """
    Busca notícias por termo de busca
    """
    # Buscar em todos os feeds e filtrar por query
    response = await get_news_from_rss(league='all', limit=100)

    # Filtrar notícias que contêm o termo de busca
    filtered_news = [
        news for news in response.items
        if query.lower() in news.title.lower() or
           query.lower() in news.description.lower()
    ]

    # Filtrar por idioma se especificado
    if language != 'all':
        filtered_news = [n for n in filtered_news if n.language == language]

    # Limitar resultados
    filtered_news = filtered_news[:limit]

    return NewsResponse(
        success=True,
        items=filtered_news,
        total=len(filtered_news),
        sources=list(set([n.source.name for n in filtered_news]))
    )
