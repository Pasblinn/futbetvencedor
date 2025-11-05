"""
🌍 CONTEXT ANALYZER - Análise de Contexto Externo
Coleta informações contextuais para enriquecer predictions

Fontes:
- RSS feeds de notícias (GloboEsporte, ESPN, etc.)
- API de clima (OpenWeatherMap - free tier)
- Base de rivalidades (local)
- Análise de tabela (motivação)
"""
import logging
import feedparser
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Match, Team

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """Analisa contexto externo de jogos"""

    # NewsAPI.org - API profissional GRATUITA
    NEWSAPI_KEY = "df39329adeeb420685d951922a52265c"
    NEWSAPI_URL = "https://newsapi.org/v2/everything"

    # RSS Feeds de notícias de futebol (backup)
    NEWS_FEEDS = [
        "https://ge.globo.com/rss/ge/futebol/",
        "https://www.espn.com.br/rss/futebol",
        "https://www.uol.com.br/esporte/futebol/index.xml",
    ]

    # Rivalidades conhecidas (expandir conforme necessário)
    RIVALRIES = {
        # Brasil
        ('Flamengo', 'Fluminense'): 'VERY_HIGH',  # Fla-Flu
        ('Flamengo', 'Vasco'): 'VERY_HIGH',
        ('Flamengo', 'Botafogo'): 'HIGH',
        ('Corinthians', 'Palmeiras'): 'VERY_HIGH',  # Derby
        ('Corinthians', 'Sao Paulo'): 'VERY_HIGH',  # Majestoso
        ('Gremio', 'Internacional'): 'VERY_HIGH',  # Gre-Nal
        ('Atletico-MG', 'Cruzeiro'): 'VERY_HIGH',  # Clássico Mineiro

        # Internacional
        ('Real Madrid', 'Barcelona'): 'VERY_HIGH',  # El Clásico
        ('Manchester United', 'Liverpool'): 'VERY_HIGH',
        ('Manchester United', 'Manchester City'): 'VERY_HIGH',
        ('Arsenal', 'Tottenham'): 'VERY_HIGH',
        ('Inter', 'AC Milan'): 'VERY_HIGH',  # Derby della Madonnina
        ('Boca Juniors', 'River Plate'): 'VERY_HIGH',  # Superclássico
    }

    def __init__(self, db: Session = None):
        self.db = db
        self._news_cache = {}
        self._news_cache_time = None

    def analyze_match_context(self, match: Match) -> Dict:
        """
        Analisa contexto completo de um jogo

        Args:
            match: Objeto Match do banco

        Returns:
            Dicionário com contexto completo
        """
        context = {
            'rivalry_level': self._analyze_rivalry(match),
            'motivation_home': self._analyze_motivation(match, 'home'),
            'motivation_away': self._analyze_motivation(match, 'away'),
            'weather': self._get_weather(match),
            'key_injuries': self._detect_injuries(match),
            'recent_news': self._get_relevant_news(match),
            'home_position': self._get_table_position(match, 'home'),
            'away_position': self._get_table_position(match, 'away'),
            'form_context': self._analyze_form_context(match),
            'analyzed_at': datetime.now().isoformat()
        }

        return context

    def _analyze_rivalry(self, match: Match) -> str:
        """Detecta nível de rivalidade entre times"""
        if not match.home_team or not match.away_team:
            return 'LOW'

        home_name = match.home_team.name
        away_name = match.away_team.name

        # Checar ambas as direções
        rivalry = self.RIVALRIES.get((home_name, away_name)) or \
                  self.RIVALRIES.get((away_name, home_name))

        if rivalry:
            logger.info(f"🔥 Rivalidade detectada: {home_name} vs {away_name} = {rivalry}")
            return rivalry

        # Checar se times da mesma cidade (provável rivalidade)
        if match.home_team.country == match.away_team.country:
            if self._same_city(home_name, away_name):
                return 'MEDIUM'

        return 'LOW'

    def _same_city(self, team1: str, team2: str) -> bool:
        """Detecta se times são da mesma cidade"""
        # Simplificado - pode expandir com base de dados de cidades
        city_keywords = {
            'Rio': ['Flamengo', 'Fluminense', 'Vasco', 'Botafogo'],
            'São Paulo': ['Corinthians', 'Palmeiras', 'Sao Paulo', 'Santos'],
            'Porto Alegre': ['Gremio', 'Internacional'],
            'Belo Horizonte': ['Atletico-MG', 'Cruzeiro'],
        }

        for city, teams in city_keywords.items():
            if team1 in teams and team2 in teams:
                return True

        return False

    def _analyze_motivation(self, match: Match, side: str) -> str:
        """
        Analisa motivação do time (título, rebaixamento, etc.)

        Args:
            match: Jogo
            side: 'home' ou 'away'

        Returns:
            Nível de motivação
        """
        team = match.home_team if side == 'home' else match.away_team

        if not team or not self.db:
            return 'NORMAL'

        # Buscar posição na tabela (se disponível)
        # Simplificado - pode integrar com API de standings
        position = self._get_table_position(match, side)

        if position:
            try:
                pos = int(position.split('º')[0]) if 'º' in position else int(position)

                # Top 4 = disputa de título/Champions
                if pos <= 4:
                    return 'TITLE_RACE'

                # Bottom 4 = luta contra rebaixamento
                elif pos >= 17:  # Assumindo 20 times
                    return 'RELEGATION_FIGHT'

                # Meio da tabela
                else:
                    return 'NORMAL'

            except:
                return 'NORMAL'

        return 'NORMAL'

    def _get_weather(self, match: Match) -> str:
        """
        Busca previsão do tempo para o jogo

        Usa OpenWeatherMap API (free tier: 1000 calls/dia)
        """
        # TODO: Implementar chamada à API de clima
        # Por enquanto, retorna placeholder
        return 'bom'

    def _detect_injuries(self, match: Match) -> List[str]:
        """
        Detecta lesões importantes através de notícias

        Returns:
            Lista de lesões relevantes
        """
        if not match.home_team or not match.away_team:
            return []

        injuries = []

        # Buscar notícias recentes
        news = self._get_relevant_news(match)

        # Palavras-chave de lesões
        injury_keywords = [
            'lesionado', 'machucado', 'contundido', 'desfalque',
            'fora', 'injured', 'out', 'suspension', 'suspenso'
        ]

        for article in news:
            article_lower = article.lower()

            # Se menciona lesão/suspensão
            if any(keyword in article_lower for keyword in injury_keywords):
                # Extrair contexto
                injuries.append(article[:100])  # Primeiros 100 chars

        return injuries[:3]  # Máximo 3 lesões mais relevantes

    def _get_relevant_news(self, match: Match) -> List[str]:
        """
        Busca notícias relevantes sobre os times via NewsAPI.org

        Returns:
            Lista de títulos de notícias
        """
        if not match.home_team or not match.away_team:
            return []

        home_name = match.home_team.name
        away_name = match.away_team.name

        # Tentar NewsAPI primeiro (melhor qualidade)
        try:
            news = self._fetch_from_newsapi(home_name, away_name)
            if news:
                logger.info(f"📰 {len(news)} notícias obtidas da NewsAPI para {home_name} vs {away_name}")
                return news
        except Exception as e:
            logger.error(f"Erro ao buscar NewsAPI: {e}")

        # Fallback: RSS feeds
        logger.info("📰 Usando RSS feeds como fallback")
        return self._fetch_from_rss(home_name, away_name)

    def _fetch_from_newsapi(self, team1: str, team2: str) -> List[str]:
        """
        Busca notícias da NewsAPI.org

        Args:
            team1: Nome do time 1
            team2: Nome do time 2

        Returns:
            Lista de notícias relevantes
        """
        # Construir query
        query = f'("{team1}" OR "{team2}") AND (futebol OR football OR soccer)'

        # Parâmetros da API
        params = {
            'apiKey': self.NEWSAPI_KEY,
            'q': query,
            'language': 'pt',  # Português
            'sortBy': 'publishedAt',  # Mais recentes primeiro
            'pageSize': 10,  # Máximo 10 artigos
            'from': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')  # Últimos 3 dias
        }

        response = requests.get(self.NEWSAPI_URL, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])

            news = []
            for article in articles:
                title = article.get('title', '')
                description = article.get('description', '')

                # Combinar título + descrição para mais contexto
                if description:
                    news.append(f"{title} - {description[:100]}")
                else:
                    news.append(title)

            return news[:5]  # Top 5 mais relevantes

        else:
            logger.warning(f"NewsAPI retornou status {response.status_code}")
            return []

    def _fetch_from_rss(self, team1: str, team2: str) -> List[str]:
        """
        Busca notícias via RSS (fallback)

        Args:
            team1: Nome do time 1
            team2: Nome do time 2

        Returns:
            Lista de notícias relevantes
        """
        # Cache de notícias (válido por 1 hora)
        if self._news_cache_time and \
           (datetime.now() - self._news_cache_time) < timedelta(hours=1):
            return self._filter_news_from_cache(team1, team2)

        # Buscar notícias frescas
        all_news = []

        for feed_url in self.NEWS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:20]:  # Últimas 20 de cada feed
                    title = entry.get('title', '')
                    all_news.append(title)

            except Exception as e:
                logger.error(f"Erro ao buscar RSS {feed_url}: {e}")

        # Atualizar cache
        self._news_cache = all_news
        self._news_cache_time = datetime.now()

        return self._filter_news_from_cache(team1, team2)

    def _filter_news_from_cache(self, team1: str, team2: str) -> List[str]:
        """Filtra notícias relevantes do cache RSS"""
        if not self._news_cache:
            return []

        relevant = []

        for news in self._news_cache:
            # Se menciona algum dos times
            if team1 in news or team2 in news:
                relevant.append(news)

        return relevant[:5]  # Máximo 5 notícias relevantes


    def _get_table_position(self, match: Match, side: str) -> Optional[str]:
        """
        Obtém posição na tabela (se disponível)

        TODO: Integrar com API de standings ou calcular localmente
        """
        return None  # Placeholder

    def _analyze_form_context(self, match: Match) -> Dict:
        """
        Analisa contexto de forma dos times

        Returns:
            Contexto de sequência, invencibilidade, etc.
        """
        if not self.db or not match.home_team or not match.away_team:
            return {}

        # Buscar últimos 5 jogos de cada time
        from app.services.analytics_service import AnalyticsService

        try:
            analytics = AnalyticsService(self.db)

            # Forma casa
            home_form = self.db.query(Match).filter(
                (Match.home_team_id == match.home_team_id) |
                (Match.away_team_id == match.home_team_id)
            ).filter(
                Match.status == 'FT'
            ).order_by(Match.match_date.desc()).limit(5).all()

            # Forma fora
            away_form = self.db.query(Match).filter(
                (Match.home_team_id == match.away_team_id) |
                (Match.away_team_id == match.away_team_id)
            ).filter(
                Match.status == 'FT'
            ).order_by(Match.match_date.desc()).limit(5).all()

            return {
                'home_last_5': self._calculate_form_string(home_form, match.home_team_id),
                'away_last_5': self._calculate_form_string(away_form, match.away_team_id),
            }

        except:
            return {}

    def _calculate_form_string(self, matches: List[Match], team_id: int) -> str:
        """Calcula string de forma (ex: WWDLW)"""
        form = []

        for m in matches:
            if m.home_team_id == team_id:
                if m.home_score > m.away_score:
                    form.append('W')
                elif m.home_score < m.away_score:
                    form.append('L')
                else:
                    form.append('D')
            else:
                if m.away_score > m.home_score:
                    form.append('W')
                elif m.away_score < m.home_score:
                    form.append('L')
                else:
                    form.append('D')

        return ''.join(form)


# Singleton global
_context_analyzer = None


def get_context_analyzer(db: Session = None) -> ContextAnalyzer:
    """Obtém instância global do Context Analyzer"""
    global _context_analyzer

    if _context_analyzer is None:
        _context_analyzer = ContextAnalyzer(db)

    if db and _context_analyzer.db is None:
        _context_analyzer.db = db

    return _context_analyzer
