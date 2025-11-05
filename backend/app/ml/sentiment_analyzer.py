import asyncio
import aiohttp
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
import logging
from textblob import TextBlob
import tweepy
from newspaper import Article
import feedparser
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Advanced sentiment analysis for football matches and teams"""

    def __init__(self):
        self.sentiment_models = {}
        self.news_sources = {
            'bbc_sport': 'http://feeds.bbci.co.uk/sport/football/rss.xml',
            'sky_sports': 'https://www.skysports.com/rss/12040',
            'espn': 'https://www.espn.com/espn/rss/soccer/news',
            'goal_com': 'https://www.goal.com/feeds/en/news',
            'football365': 'https://www.football365.com/feed'
        }

        # Social media APIs
        self.twitter_api = None
        self.reddit_api = None

        # Initialize sentiment analysis models
        self._initialize_models()

    def _initialize_models(self):
        """Initialize various sentiment analysis models"""
        try:
            # Hugging Face transformer model for sports sentiment
            self.sentiment_models['sports'] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )

            # Financial sentiment model (useful for transfer news impact)
            self.sentiment_models['financial'] = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert"
            )

            logger.info("Sentiment analysis models initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing sentiment models: {e}")
            # Fallback to TextBlob
            self.sentiment_models['textblob'] = TextBlob

    async def analyze_team_sentiment(self, team_name: str, days_back: int = 7) -> Dict:
        """Analyze sentiment around a team from multiple sources"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        sentiment_data = {
            'team_name': team_name,
            'analysis_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'sources': {},
            'overall_sentiment': {},
            'key_topics': [],
            'sentiment_trend': []
        }

        # Analyze news articles
        news_sentiment = await self._analyze_news_sentiment(team_name, start_date, end_date)
        sentiment_data['sources']['news'] = news_sentiment

        # Analyze social media
        social_sentiment = await self._analyze_social_sentiment(team_name, start_date, end_date)
        sentiment_data['sources']['social_media'] = social_sentiment

        # Analyze transfer rumors and financial news
        transfer_sentiment = await self._analyze_transfer_sentiment(team_name, start_date, end_date)
        sentiment_data['sources']['transfers'] = transfer_sentiment

        # Calculate overall sentiment
        sentiment_data['overall_sentiment'] = self._calculate_overall_sentiment(sentiment_data['sources'])

        # Extract key topics and trends
        sentiment_data['key_topics'] = self._extract_key_topics(sentiment_data['sources'])
        sentiment_data['sentiment_trend'] = self._calculate_sentiment_trend(sentiment_data['sources'])

        return sentiment_data

    async def _analyze_news_sentiment(self, team_name: str, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze sentiment from news sources"""
        news_sentiment = {
            'articles_analyzed': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'average_sentiment': 0.0,
            'sentiment_distribution': {},
            'key_articles': []
        }

        articles = await self._fetch_news_articles(team_name, start_date, end_date)

        for article in articles:
            try:
                sentiment_score = await self._analyze_text_sentiment(article['content'])

                news_sentiment['articles_analyzed'] += 1

                if sentiment_score['compound'] > 0.1:
                    news_sentiment['positive_count'] += 1
                elif sentiment_score['compound'] < -0.1:
                    news_sentiment['negative_count'] += 1
                else:
                    news_sentiment['neutral_count'] += 1

                # Store key articles with strong sentiment
                if abs(sentiment_score['compound']) > 0.3:
                    news_sentiment['key_articles'].append({
                        'title': article['title'],
                        'url': article['url'],
                        'sentiment_score': sentiment_score,
                        'published_date': article['published_date']
                    })

            except Exception as e:
                logger.warning(f"Error analyzing article sentiment: {e}")

        # Calculate averages
        if news_sentiment['articles_analyzed'] > 0:
            total_articles = news_sentiment['articles_analyzed']
            news_sentiment['sentiment_distribution'] = {
                'positive': news_sentiment['positive_count'] / total_articles,
                'negative': news_sentiment['negative_count'] / total_articles,
                'neutral': news_sentiment['neutral_count'] / total_articles
            }

        return news_sentiment

    async def _analyze_social_sentiment(self, team_name: str, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze sentiment from social media"""
        social_sentiment = {
            'posts_analyzed': 0,
            'platforms': {},
            'overall_sentiment': 0.0,
            'engagement_sentiment': {},
            'trending_topics': []
        }

        # Twitter analysis
        if self.twitter_api:
            twitter_data = await self._analyze_twitter_sentiment(team_name, start_date, end_date)
            social_sentiment['platforms']['twitter'] = twitter_data

        # Reddit analysis
        reddit_data = await self._analyze_reddit_sentiment(team_name, start_date, end_date)
        social_sentiment['platforms']['reddit'] = reddit_data

        # Calculate overall social sentiment
        platform_sentiments = []
        for platform_data in social_sentiment['platforms'].values():
            if 'average_sentiment' in platform_data:
                platform_sentiments.append(platform_data['average_sentiment'])

        if platform_sentiments:
            social_sentiment['overall_sentiment'] = np.mean(platform_sentiments)

        return social_sentiment

    async def _analyze_transfer_sentiment(self, team_name: str, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze sentiment around transfer news and financial developments"""
        transfer_sentiment = {
            'transfer_rumors': [],
            'financial_news': [],
            'market_impact': 0.0,
            'fan_reaction': 0.0
        }

        # Search for transfer-related news
        transfer_keywords = [
            f"{team_name} transfer",
            f"{team_name} signing",
            f"{team_name} bid",
            f"{team_name} rumor"
        ]

        for keyword in transfer_keywords:
            articles = await self._fetch_news_articles(keyword, start_date, end_date)

            for article in articles[:5]:  # Limit to top 5 per keyword
                try:
                    # Use financial sentiment model for transfer news
                    financial_sentiment = await self._analyze_financial_sentiment(article['content'])

                    transfer_sentiment['transfer_rumors'].append({
                        'title': article['title'],
                        'sentiment': financial_sentiment,
                        'impact_score': abs(financial_sentiment['compound']),
                        'published_date': article['published_date']
                    })

                except Exception as e:
                    logger.warning(f"Error analyzing transfer sentiment: {e}")

        # Calculate market impact
        if transfer_sentiment['transfer_rumors']:
            impact_scores = [rumor['impact_score'] for rumor in transfer_sentiment['transfer_rumors']]
            transfer_sentiment['market_impact'] = np.mean(impact_scores)

        return transfer_sentiment

    async def _fetch_news_articles(self, search_term: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch news articles from RSS feeds and news APIs"""
        articles = []

        # Fetch from RSS feeds
        for source_name, feed_url in self.news_sources.items():
            try:
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:10]:  # Limit per source
                    # Check if article is relevant and within date range
                    if search_term.lower() in entry.title.lower() or search_term.lower() in entry.description.lower():
                        # Parse published date
                        try:
                            pub_date = datetime(*entry.published_parsed[:6])
                            if start_date <= pub_date <= end_date:
                                # Fetch full article content
                                content = await self._fetch_article_content(entry.link)

                                articles.append({
                                    'title': entry.title,
                                    'url': entry.link,
                                    'content': content,
                                    'source': source_name,
                                    'published_date': pub_date
                                })
                        except Exception:
                            continue

            except Exception as e:
                logger.warning(f"Error fetching from {source_name}: {e}")

        # Fetch from News API (if configured)
        news_api_articles = await self._fetch_from_news_api(search_term, start_date, end_date)
        articles.extend(news_api_articles)

        return articles

    async def _fetch_article_content(self, url: str) -> str:
        """Fetch and extract main content from article URL"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            return article.text
        except Exception as e:
            logger.warning(f"Error fetching article content from {url}: {e}")
            return ""

    async def _fetch_from_news_api(self, search_term: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch articles from News API"""
        # This would require News API key and implementation
        # Placeholder for now
        return []

    async def _analyze_twitter_sentiment(self, team_name: str, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze Twitter sentiment using Twitter API v2"""
        twitter_sentiment = {
            'tweets_analyzed': 0,
            'average_sentiment': 0.0,
            'engagement_metrics': {},
            'trending_hashtags': []
        }

        # This would require Twitter API v2 implementation
        # Placeholder for now
        return twitter_sentiment

    async def _analyze_reddit_sentiment(self, team_name: str, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze Reddit sentiment from relevant subreddits"""
        reddit_sentiment = {
            'posts_analyzed': 0,
            'comments_analyzed': 0,
            'average_sentiment': 0.0,
            'subreddit_breakdown': {}
        }

        # Reddit API implementation would go here
        # Placeholder for now
        return reddit_sentiment

    async def _analyze_text_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text using multiple models"""
        if not text or len(text.strip()) < 10:
            return {'compound': 0.0, 'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}

        sentiment_scores = {}

        # Use Hugging Face model if available
        if 'sports' in self.sentiment_models:
            try:
                result = self.sentiment_models['sports'](text[:512])  # Limit text length

                # Convert to standard format
                label = result[0]['label'].lower()
                score = result[0]['score']

                if 'positive' in label:
                    sentiment_scores['hf_positive'] = score
                    sentiment_scores['hf_negative'] = 0.0
                elif 'negative' in label:
                    sentiment_scores['hf_positive'] = 0.0
                    sentiment_scores['hf_negative'] = score
                else:
                    sentiment_scores['hf_positive'] = 0.0
                    sentiment_scores['hf_negative'] = 0.0

            except Exception as e:
                logger.warning(f"Error with HuggingFace sentiment analysis: {e}")

        # Use TextBlob as fallback
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            sentiment_scores['textblob_polarity'] = polarity
            sentiment_scores['textblob_subjectivity'] = subjectivity

        except Exception as e:
            logger.warning(f"Error with TextBlob sentiment analysis: {e}")

        # Combine scores
        if sentiment_scores:
            # Calculate compound score
            if 'hf_positive' in sentiment_scores:
                compound = sentiment_scores['hf_positive'] - sentiment_scores['hf_negative']
            elif 'textblob_polarity' in sentiment_scores:
                compound = sentiment_scores['textblob_polarity']
            else:
                compound = 0.0

            return {
                'compound': compound,
                'positive': max(0, compound),
                'negative': max(0, -compound),
                'neutral': 1 - abs(compound),
                'raw_scores': sentiment_scores
            }

        return {'compound': 0.0, 'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}

    async def _analyze_financial_sentiment(self, text: str) -> Dict:
        """Analyze financial sentiment for transfer news"""
        if 'financial' in self.sentiment_models:
            try:
                result = self.sentiment_models['financial'](text[:512])

                label = result[0]['label'].lower()
                score = result[0]['score']

                # Convert FinBERT labels to sentiment scores
                if 'positive' in label:
                    return {'compound': score, 'label': 'positive'}
                elif 'negative' in label:
                    return {'compound': -score, 'label': 'negative'}
                else:
                    return {'compound': 0.0, 'label': 'neutral'}

            except Exception as e:
                logger.warning(f"Error with financial sentiment analysis: {e}")

        # Fallback to regular sentiment analysis
        return await self._analyze_text_sentiment(text)

    def _calculate_overall_sentiment(self, sources: Dict) -> Dict:
        """Calculate overall sentiment from all sources"""
        sentiment_scores = []
        weights = {'news': 0.4, 'social_media': 0.4, 'transfers': 0.2}

        overall = {
            'compound_score': 0.0,
            'confidence': 0.0,
            'primary_driver': '',
            'sentiment_label': 'neutral'
        }

        for source_name, source_data in sources.items():
            weight = weights.get(source_name, 0.1)

            if source_name == 'news' and 'average_sentiment' in source_data:
                sentiment_scores.append((source_data['average_sentiment'], weight))
            elif source_name == 'social_media' and 'overall_sentiment' in source_data:
                sentiment_scores.append((source_data['overall_sentiment'], weight))
            elif source_name == 'transfers' and 'market_impact' in source_data:
                # Convert market impact to sentiment
                impact = source_data['market_impact']
                # Positive transfers generally create positive sentiment
                sentiment = impact * 0.5  # Scaled down as transfers can be uncertain
                sentiment_scores.append((sentiment, weight))

        if sentiment_scores:
            # Weighted average
            total_weight = sum(weight for _, weight in sentiment_scores)
            if total_weight > 0:
                weighted_sentiment = sum(score * weight for score, weight in sentiment_scores) / total_weight
                overall['compound_score'] = weighted_sentiment

                # Determine primary driver
                max_impact = max(sentiment_scores, key=lambda x: abs(x[0] * x[1]))
                source_index = sentiment_scores.index(max_impact)
                source_names = list(sources.keys())
                overall['primary_driver'] = source_names[source_index] if source_index < len(source_names) else 'unknown'

                # Calculate confidence based on consistency
                score_variance = np.var([score for score, _ in sentiment_scores])
                overall['confidence'] = max(0, 1 - score_variance)

                # Sentiment label
                if weighted_sentiment > 0.1:
                    overall['sentiment_label'] = 'positive'
                elif weighted_sentiment < -0.1:
                    overall['sentiment_label'] = 'negative'
                else:
                    overall['sentiment_label'] = 'neutral'

        return overall

    def _extract_key_topics(self, sources: Dict) -> List[Dict]:
        """Extract key topics and themes from sentiment analysis"""
        topics = []

        # Extract from news articles
        if 'news' in sources and 'key_articles' in sources['news']:
            for article in sources['news']['key_articles']:
                topics.append({
                    'topic': article['title'],
                    'sentiment': article['sentiment_score']['compound'],
                    'source': 'news',
                    'relevance': abs(article['sentiment_score']['compound'])
                })

        # Extract from transfer news
        if 'transfers' in sources and 'transfer_rumors' in sources['transfers']:
            for rumor in sources['transfers']['transfer_rumors']:
                topics.append({
                    'topic': rumor['title'],
                    'sentiment': rumor['sentiment']['compound'],
                    'source': 'transfers',
                    'relevance': rumor['impact_score']
                })

        # Sort by relevance
        topics.sort(key=lambda x: x['relevance'], reverse=True)
        return topics[:10]  # Return top 10 topics

    def _calculate_sentiment_trend(self, sources: Dict) -> List[Dict]:
        """Calculate sentiment trend over time"""
        # This would require time-series data
        # Placeholder implementation
        trend = []

        # For now, return a simple trend based on current sentiment
        current_time = datetime.now()

        for i in range(7):  # Last 7 days
            date = current_time - timedelta(days=i)

            # Mock trend data - in real implementation, this would use historical data
            trend.append({
                'date': date.strftime('%Y-%m-%d'),
                'sentiment_score': np.random.normal(0, 0.3),  # Random sentiment for demo
                'confidence': 0.7
            })

        return sorted(trend, key=lambda x: x['date'])

    async def get_match_sentiment_impact(self, home_team: str, away_team: str, match_date: datetime) -> Dict:
        """Analyze sentiment impact on upcoming match"""
        # Analyze sentiment for both teams
        home_sentiment = await self.analyze_team_sentiment(home_team, days_back=3)
        away_sentiment = await self.analyze_team_sentiment(away_team, days_back=3)

        # Calculate sentiment advantage
        home_score = home_sentiment['overall_sentiment'].get('compound_score', 0)
        away_score = away_sentiment['overall_sentiment'].get('compound_score', 0)

        sentiment_advantage = home_score - away_score

        return {
            'home_team_sentiment': home_sentiment,
            'away_team_sentiment': away_sentiment,
            'sentiment_advantage': sentiment_advantage,
            'predicted_impact': {
                'motivation_boost': max(0, sentiment_advantage * 0.1),
                'pressure_factor': abs(sentiment_advantage) * 0.05,
                'fan_support_impact': sentiment_advantage * 0.08
            },
            'key_narratives': self._identify_match_narratives(home_sentiment, away_sentiment),
            'recommendation': self._generate_sentiment_recommendation(sentiment_advantage)
        }

    def _identify_match_narratives(self, home_sentiment: Dict, away_sentiment: Dict) -> List[str]:
        """Identify key narratives affecting the match"""
        narratives = []

        # Check for significant sentiment differences
        home_score = home_sentiment['overall_sentiment'].get('compound_score', 0)
        away_score = away_sentiment['overall_sentiment'].get('compound_score', 0)

        if home_score > 0.3:
            narratives.append(f"Home team riding wave of positive sentiment")
        elif home_score < -0.3:
            narratives.append(f"Home team under pressure from negative coverage")

        if away_score > 0.3:
            narratives.append(f"Away team confident after positive recent news")
        elif away_score < -0.3:
            narratives.append(f"Away team facing criticism and low morale")

        # Check for transfer activity
        if 'transfers' in home_sentiment['sources']:
            if home_sentiment['sources']['transfers'].get('market_impact', 0) > 0.5:
                narratives.append("Home team boosted by recent transfer activity")

        if 'transfers' in away_sentiment['sources']:
            if away_sentiment['sources']['transfers'].get('market_impact', 0) > 0.5:
                narratives.append("Away team strengthened by new signings")

        return narratives

    def _generate_sentiment_recommendation(self, sentiment_advantage: float) -> Dict:
        """Generate recommendation based on sentiment analysis"""
        if abs(sentiment_advantage) < 0.1:
            impact = "minimal"
            recommendation = "Sentiment is neutral - focus on other factors"
        elif sentiment_advantage > 0.3:
            impact = "significant"
            recommendation = "Strong positive sentiment for home team - consider home win"
        elif sentiment_advantage < -0.3:
            impact = "significant"
            recommendation = "Strong positive sentiment for away team - consider away win"
        elif sentiment_advantage > 0.1:
            impact = "moderate"
            recommendation = "Moderate positive sentiment for home team"
        else:
            impact = "moderate"
            recommendation = "Moderate positive sentiment for away team"

        return {
            'impact_level': impact,
            'recommendation': recommendation,
            'confidence': min(0.8, abs(sentiment_advantage) * 2),
            'weight_in_prediction': max(0.05, min(0.15, abs(sentiment_advantage)))
        }