import httpx
from typing import Dict, Optional
from datetime import datetime
from app.core.config import settings
from app.core.redis import redis_client
import json

class WeatherService:
    def __init__(self):
        self.base_url = settings.WEATHER_API_BASE_URL
        self.api_key = settings.WEATHER_API_KEY
        self.cache_ttl = 1800  # 30 minutes

    async def get_weather_by_city(self, city: str, country_code: str = None) -> Dict:
        """Get current weather for a city"""
        location = f"{city},{country_code}" if country_code else city
        cache_key = f"weather:current:{location}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/weather",
                params={
                    "q": location,
                    "appid": self.api_key,
                    "units": "metric"
                }
            )

            if response.status_code == 200:
                data = response.json()
                weather_info = self._parse_weather_data(data)
                await redis_client.setex(cache_key, self.cache_ttl, json.dumps(weather_info))
                return weather_info

            raise Exception(f"Failed to fetch weather: {response.status_code}")

    async def get_weather_by_coordinates(self, lat: float, lon: float) -> Dict:
        """Get current weather by coordinates"""
        cache_key = f"weather:coords:{lat}:{lon}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric"
                }
            )

            if response.status_code == 200:
                data = response.json()
                weather_info = self._parse_weather_data(data)
                await redis_client.setex(cache_key, self.cache_ttl, json.dumps(weather_info))
                return weather_info

            raise Exception(f"Failed to fetch weather: {response.status_code}")

    async def get_forecast_by_city(self, city: str, country_code: str = None, days: int = 5) -> Dict:
        """Get weather forecast for a city"""
        location = f"{city},{country_code}" if country_code else city
        cache_key = f"weather:forecast:{location}:{days}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/forecast",
                params={
                    "q": location,
                    "appid": self.api_key,
                    "units": "metric",
                    "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
                }
            )

            if response.status_code == 200:
                data = response.json()
                forecast_info = self._parse_forecast_data(data)
                await redis_client.setex(cache_key, 3600, json.dumps(forecast_info))  # Cache for 1 hour
                return forecast_info

            raise Exception(f"Failed to fetch forecast: {response.status_code}")

    async def get_match_weather(self, venue_city: str, country_code: str, match_datetime: datetime) -> Dict:
        """Get weather forecast for a specific match"""
        cache_key = f"weather:match:{venue_city}:{country_code}:{match_datetime.isoformat()}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        # If match is within 5 days, get forecast
        time_diff = match_datetime - datetime.now()

        if time_diff.days <= 5:
            forecast = await self.get_forecast_by_city(venue_city, country_code)

            # Find the closest forecast to match time
            match_weather = self._find_closest_forecast(forecast, match_datetime)

            if match_weather:
                match_weather["impact_assessment"] = self._assess_weather_impact(match_weather)
                await redis_client.setex(cache_key, 3600, json.dumps(match_weather))
                return match_weather

        # If no forecast available, return current weather with warning
        current_weather = await self.get_weather_by_city(venue_city, country_code)
        current_weather["is_forecast"] = False
        current_weather["warning"] = "Using current weather - match forecast not available"

        return current_weather

    def _parse_weather_data(self, data: Dict) -> Dict:
        """Parse OpenWeatherMap current weather response"""
        return {
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"].get("speed", 0),
            "wind_direction": data["wind"].get("deg", 0),
            "weather_condition": data["weather"][0]["main"],
            "weather_description": data["weather"][0]["description"],
            "visibility": data.get("visibility", 10000) / 1000,  # Convert to km
            "clouds": data["clouds"]["all"],
            "rain": data.get("rain", {}).get("1h", 0),
            "snow": data.get("snow", {}).get("1h", 0),
            "timestamp": datetime.now().isoformat(),
            "city": data["name"],
            "country": data["sys"]["country"]
        }

    def _parse_forecast_data(self, data: Dict) -> Dict:
        """Parse OpenWeatherMap forecast response"""
        forecasts = []

        for forecast in data["list"]:
            forecasts.append({
                "datetime": forecast["dt_txt"],
                "temperature": forecast["main"]["temp"],
                "feels_like": forecast["main"]["feels_like"],
                "humidity": forecast["main"]["humidity"],
                "pressure": forecast["main"]["pressure"],
                "wind_speed": forecast["wind"].get("speed", 0),
                "wind_direction": forecast["wind"].get("deg", 0),
                "weather_condition": forecast["weather"][0]["main"],
                "weather_description": forecast["weather"][0]["description"],
                "visibility": forecast.get("visibility", 10000) / 1000,
                "clouds": forecast["clouds"]["all"],
                "rain": forecast.get("rain", {}).get("3h", 0),
                "snow": forecast.get("snow", {}).get("3h", 0),
                "pop": forecast.get("pop", 0)  # Probability of precipitation
            })

        return {
            "city": data["city"]["name"],
            "country": data["city"]["country"],
            "forecasts": forecasts
        }

    def _find_closest_forecast(self, forecast_data: Dict, target_datetime: datetime) -> Optional[Dict]:
        """Find the forecast closest to the target datetime"""
        if not forecast_data.get("forecasts"):
            return None

        closest_forecast = None
        min_diff = float('inf')

        for forecast in forecast_data["forecasts"]:
            forecast_time = datetime.fromisoformat(forecast["datetime"])
            time_diff = abs((forecast_time - target_datetime).total_seconds())

            if time_diff < min_diff:
                min_diff = time_diff
                closest_forecast = forecast

        if closest_forecast:
            closest_forecast["city"] = forecast_data["city"]
            closest_forecast["country"] = forecast_data["country"]
            closest_forecast["is_forecast"] = True

        return closest_forecast

    def _assess_weather_impact(self, weather: Dict) -> Dict:
        """Assess the impact of weather conditions on match play"""
        impact = {
            "overall_score": 0.0,  # 0-1 scale (0 = no impact, 1 = severe impact)
            "factors": {},
            "recommendations": []
        }

        # Temperature impact
        temp = weather.get("temperature", 20)
        if temp < 0:
            impact["factors"]["temperature"] = 0.8
            impact["recommendations"].append("Very cold conditions may affect player performance")
        elif temp < 5:
            impact["factors"]["temperature"] = 0.6
            impact["recommendations"].append("Cold conditions may slow the game")
        elif temp > 35:
            impact["factors"]["temperature"] = 0.7
            impact["recommendations"].append("Very hot conditions may tire players faster")
        elif temp > 30:
            impact["factors"]["temperature"] = 0.4
            impact["recommendations"].append("Hot conditions may affect stamina")
        else:
            impact["factors"]["temperature"] = 0.0

        # Wind impact
        wind_speed = weather.get("wind_speed", 0)
        if wind_speed > 15:
            impact["factors"]["wind"] = 0.8
            impact["recommendations"].append("Strong winds will significantly affect ball trajectory")
        elif wind_speed > 10:
            impact["factors"]["wind"] = 0.5
            impact["recommendations"].append("Moderate winds may affect long passes and shots")
        elif wind_speed > 7:
            impact["factors"]["wind"] = 0.2
            impact["recommendations"].append("Light winds may slightly affect aerial play")
        else:
            impact["factors"]["wind"] = 0.0

        # Precipitation impact
        rain = weather.get("rain", 0)
        snow = weather.get("snow", 0)

        if snow > 0:
            impact["factors"]["precipitation"] = 1.0
            impact["recommendations"].append("Snow conditions heavily favor Under goals and defensive play")
        elif rain > 5:
            impact["factors"]["precipitation"] = 0.9
            impact["recommendations"].append("Heavy rain favors Under goals and increases defensive errors")
        elif rain > 2:
            impact["factors"]["precipitation"] = 0.6
            impact["recommendations"].append("Moderate rain may reduce pace and increase mistakes")
        elif rain > 0:
            impact["factors"]["precipitation"] = 0.3
            impact["recommendations"].append("Light rain may slightly affect ball control")
        else:
            impact["factors"]["precipitation"] = 0.0

        # Visibility impact
        visibility = weather.get("visibility", 10)
        if visibility < 1:
            impact["factors"]["visibility"] = 1.0
            impact["recommendations"].append("Very poor visibility - match may be postponed")
        elif visibility < 3:
            impact["factors"]["visibility"] = 0.7
            impact["recommendations"].append("Poor visibility affects long-range play")
        elif visibility < 6:
            impact["factors"]["visibility"] = 0.3
            impact["recommendations"].append("Reduced visibility may affect passing accuracy")
        else:
            impact["factors"]["visibility"] = 0.0

        # Calculate overall impact
        impact["overall_score"] = max(impact["factors"].values()) if impact["factors"] else 0.0

        # Match style predictions based on weather
        if impact["overall_score"] > 0.6:
            impact["style_prediction"] = "defensive_slow"
            impact["betting_implications"] = ["Under 2.5 goals more likely", "More corners due to defensive play", "Higher chance of draws"]
        elif impact["overall_score"] > 0.3:
            impact["style_prediction"] = "slightly_affected"
            impact["betting_implications"] = ["Slight favor to Under goals", "May increase cards due to poor conditions"]
        else:
            impact["style_prediction"] = "normal"
            impact["betting_implications"] = ["Weather should not significantly affect outcome"]

        return impact