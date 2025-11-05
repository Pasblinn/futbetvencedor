#!/usr/bin/env python3
"""
Script para buscar APENAS 2 jogos específicos - rate limit friendly
Manchester City vs Burnley e Chelsea vs Brighton - 27/09 11:00 Brasília
"""
import requests
import json
from datetime import datetime
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.config import settings

# API Keys from .env
FOOTBALL_DATA_API_KEY = settings.FOOTBALL_DATA_API_KEY

if not FOOTBALL_DATA_API_KEY:
    raise ValueError("FOOTBALL_DATA_API_KEY não configurada. Configure no arquivo .env")

def fetch_premier_league_matches_tomorrow():
    """Fetch Premier League matches for tomorrow (27/09) - rate limit friendly"""
    print("🔍 BUSCANDO APENAS 2 JOGOS ESPECÍFICOS - Premier League 27/09...")

    headers = {
        'X-Auth-Token': FOOTBALL_DATA_API_KEY
    }

    # Premier League competition ID: PL
    # Date: 2025-09-27 (tomorrow)
    target_date = "2025-09-27"
    url = f"https://api.football-data.org/v4/competitions/PL/matches?dateFrom={target_date}&dateTo={target_date}"

    try:
        print(f"📡 Request URL: {url}")
        response = requests.get(url, headers=headers)
        print(f"📊 API Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            matches = data.get('matches', [])
            print(f"🎯 Total Premier League matches tomorrow: {len(matches)}")

            # Filter for our specific matches
            target_matches = []

            for match in matches:
                home_team = match.get('homeTeam', {}).get('name', '')
                away_team = match.get('awayTeam', {}).get('name', '')
                match_time = match.get('utcDate', '')

                print(f"  📋 Found: {home_team} vs {away_team} at {match_time}")

                # Check for Manchester City vs Burnley
                if (('Manchester City' in home_team or 'City' in home_team) and
                    ('Burnley' in away_team)) or \
                   (('Burnley' in home_team) and
                    ('Manchester City' in away_team or 'City' in away_team)):
                    print(f"  ✅ FOUND TARGET: Manchester City vs Burnley")
                    target_matches.append({
                        'match_type': 'Manchester City vs Burnley',
                        'data': match
                    })

                # Check for Chelsea vs Brighton
                if (('Chelsea' in home_team) and
                    ('Brighton' in away_team or 'Hove' in away_team)) or \
                   (('Brighton' in home_team or 'Hove' in home_team) and
                    ('Chelsea' in away_team)):
                    print(f"  ✅ FOUND TARGET: Chelsea vs Brighton")
                    target_matches.append({
                        'match_type': 'Chelsea vs Brighton',
                        'data': match
                    })

            return target_matches

        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    print("🚀 BUSCA ESPECÍFICA - 2 JOGOS APENAS")
    print("🎯 Target: Man City vs Burnley + Chelsea vs Brighton")
    print("📅 Date: 27/09/2025 11:00 Brasília")
    print("=" * 50)

    # Create temp directory if needed
    os.makedirs('/tmp/app', exist_ok=True)

    # Fetch the specific matches
    target_matches = fetch_premier_league_matches_tomorrow()

    if target_matches:
        print(f"\n✅ SUCCESS: Found {len(target_matches)} target matches")

        for match_info in target_matches:
            match_type = match_info['match_type']
            match_data = match_info['data']

            home_team = match_data.get('homeTeam', {}).get('name', '')
            away_team = match_data.get('awayTeam', {}).get('name', '')
            match_time = match_data.get('utcDate', '')

            print(f"  🎯 {match_type}")
            print(f"     Teams: {home_team} vs {away_team}")
            print(f"     Time: {match_time}")
            print()

        # Save to file
        output_file = '/tmp/app/specific_matches_27_09.json'
        with open(output_file, 'w') as f:
            json.dump(target_matches, f, indent=2, default=str)
        print(f"📁 Data saved to: {output_file}")

        # Also save summary
        summary = {
            'search_date': '2025-09-27',
            'search_time': datetime.now().isoformat(),
            'total_found': len(target_matches),
            'matches': [
                {
                    'type': match['match_type'],
                    'home_team': match['data'].get('homeTeam', {}).get('name'),
                    'away_team': match['data'].get('awayTeam', {}).get('name'),
                    'utc_time': match['data'].get('utcDate'),
                    'status': match['data'].get('status')
                }
                for match in target_matches
            ]
        }

        summary_file = '/tmp/app/matches_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"📊 Summary saved to: {summary_file}")

    else:
        print("\n❌ FAILED: No target matches found")
        print("⚠️  This might be because:")
        print("   - API rate limit reached")
        print("   - Matches not scheduled for that date")
        print("   - Team names don't match exactly")

    print("\n🎯 SPECIFIC SEARCH COMPLETED!")

if __name__ == "__main__":
    main()