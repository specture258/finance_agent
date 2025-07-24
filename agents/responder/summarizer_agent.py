import requests
import json
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from config import HYPERCLOVA_URL, HYPERCLOVA_API_KEY, HYPERCLOVA_API_GATEWAY_KEY, generate_request_id

class SummarizerAgent(BaseAgent):
    def __init__(self):
        super().__init__("RealSummarizer")
        
        # HyperCLOVA API 사용 가능 여부 확인
        self.hyperclova_available = bool(HYPERCLOVA_API_KEY and HYPERCLOVA_API_GATEWAY_KEY)
        
        if self.hyperclova_available:
            self.log_info("HyperCLOVA API 사용 가능")
        else:
            self.log_info("HyperCLOVA API 키가 없어 기본 요약 모드로 동작")
    
    def call_hyperclova(self, prompt: str, max_tokens: int = 500) -> str:
        """HyperCLOVA API 호출"""
        if not self.hyperclova_available:
            return self._fallback_summary(prompt)
        
        try:
            headers = {
                'X-NCP-CLOVASTUDIO-API-KEY': HYPERCLOVA_API_KEY,
                'X-NCP-APIGW-API-KEY': HYPERCLOVA_API_GATEWAY_KEY,
                'X-NCP-CLOVASTUDIO-REQUEST-ID': generate_request_id(),
                'Content-Type': 'application/json'
            }
            
            data = {
                'messages': [
                    {
                        'role': 'system',
                        'content': '''당신은 전문 주식 애널리스트입니다. 
실시간 주식 데이터를 바탕으로 투자자들이 이해하기 쉽게 분석하고 요약해주세요.
- 객관적이고 정확한 정보 전달
- 투자 위험에 대한 적절한 경고
- 쉽고 명확한 표현 사용'''
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'topP': 0.8,
                'topK': 0,
                'maxTokens': max_tokens,
                'temperature': 0.3,  # 정확성을 위해 낮게 설정
                'repeatPenalty': 5.0,
                'stopBefore': [],
                'includeAiFilters': True
            }
            
            response = requests.post(HYPERCLOVA_URL, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['result']['message']['content']
            else:
                self.log_error(f"HyperCLOVA API 호출 실패: {response.status_code}")
                return self._fallback_summary(prompt)
                
        except Exception as e:
            self.log_error(f"HyperCLOVA API 호출 중 오류: {str(e)}")
            return self._fallback_summary(prompt)
    
    def _fallback_summary(self, prompt: str) -> str:
        """API 실패시 대체 요약"""
        if "실시간" in prompt or "현재가" in prompt:
            return "실시간 주식 데이터를 조회했습니다. 시장 상황을 종합적으로 고려하여 투자 결정하시기 바랍니다."
        elif "상승률" in prompt:
            return "상승률 상위 종목들을 조회했습니다. 높은 상승률이 지속되지 않을 수 있으니 신중한 판단이 필요합니다."
        elif "하락률" in prompt:
            return "하락률이 큰 종목들을 조회했습니다. 추가 하락 가능성을 고려하여 신중하게 접근하시기 바랍니다."
        else:
            return "요청하신 주식 정보를 실시간 데이터로 조회했습니다."
    
    def analyze_market_sentiment(self, stock_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """시장 심리 분석"""
        if not stock_data:
            return {"sentiment": "중립", "analysis": "데이터 부족"}
        
        up_count = len([s for s in stock_data if s.get("change_rate", 0) > 0])
        down_count = len([s for s in stock_data if s.get("change_rate", 0) < 0])
        total = len(stock_data)
        
        up_ratio = up_count / total if total > 0 else 0
        
        if up_ratio > 0.7:
            sentiment = "매우 긍정적"
        elif up_ratio > 0.6:
            sentiment = "긍정적"
        elif up_ratio > 0.4:
            sentiment = "중립적"
        elif up_ratio > 0.3:
            sentiment = "부정적"
        else:
            sentiment = "매우 부정적"
        
        avg_change = sum(s.get("change_rate", 0) for s in stock_data) / total if total > 0 else 0
        
        return {
            "sentiment": sentiment,
            "up_ratio": up_ratio,
            "avg_change": avg_change,
            "up_count": up_count,
            "down_count": down_count,
            "total": total
        }
    
    def format_stock_summary(self, stock_data: Dict[str, Any], query_type: str = "single") -> str:
        """개별 주식 데이터 요약"""
        if "error" in stock_data:
            return f"❌ 오류: {stock_data['error']}"
        
        symbol = stock_data.get('symbol', '알 수 없음')
        current_price = stock_data.get('current_price', 0)
        change_rate = stock_data.get('change_rate', 0)
        volume = stock_data.get('volume', 0)
        data_source = stock_data.get('data_source', 'unknown')
        
        # HyperCLOVA를 사용한 분석
        prompt = f"""
다음 실시간 주식 정보를 분석해서 투자자에게 유용한 인사이트를 제공해주세요:

종목: {symbol}
현재가: {current_price:,}원
변동률: {change_rate:+.2f}%
거래량: {volume:,}주

분석 요청사항:
1. 현재 가격 수준에 대한 평가
2. 거래량의 의미
3. 투자시 고려사항

간결하고 명확하게 2-3줄로 요약해주세요.
"""
        
        ai_analysis = self.call_hyperclova(prompt, 300)
        
        # 기본 정보 표시
        trend_emoji = "📈" if change_rate > 0 else "📉" if change_rate < 0 else "➡️"
        
        result = f"{trend_emoji} **{symbol} 실시간 분석**\n\n"
        result += f"💰 현재가: {current_price:,}원 ({change_rate:+.2f}%)\n"
        result += f"📊 거래량: {volume:,}주\n"
        result += f"📡 데이터: {data_source}\n\n"
        result += f"🤖 **AI 분석**: {ai_analysis}"
        
        return result
    
    def format_ranking_summary(self, stock_list: List[Dict[str, Any]], query_type: str = "ranking") -> str:
        """순위 데이터 요약"""
        if not stock_list:
            return "❌ 조회된 종목이 없습니다."
        
        # 시장 심리 분석
        market_sentiment = self.analyze_market_sentiment(stock_list)
        
        # 상위 종목들 정보
        top_stocks_info = []
        for i, stock in enumerate(stock_list[:5], 1):
            symbol = stock.get('symbol', '알 수 없음')
            price = stock.get('current_price', 0)
            change = stock.get('change_rate', 0)
            volume = stock.get('volume', 0)
            
            top_stocks_info.append({
                "rank": i,
                "symbol": symbol,
                "price": price,
                "change": change,
                "volume": volume
            })
        
        # HyperCLOVA를 사용한 시장 분석
        prompt = f"""
다음 실시간 주식 순위 데이터를 분석해서 현재 시장 상황을 요약해주세요:

시장 심리: {market_sentiment['sentiment']}
상승 종목: {market_sentiment['up_count']}개
하락 종목: {market_sentiment['down_count']}개
평균 변동률: {market_sentiment['avg_change']:.2f}%

상위 5개 종목:
"""
        
        for stock in top_stocks_info:
            prompt += f"{stock['rank']}. {stock['symbol']}: {stock['price']:,}원 ({stock['change']:+.2f}%)\n"
        
        prompt += """
현재 시장 상황과 투자자가 주목해야 할 점을 3-4줄로 분석해주세요.
"""
        
        ai_analysis = self.call_hyperclova(prompt, 400)
        
        # 응답 구성
        sentiment_emoji = {
            '매우 긍정적': '🚀',
            '긍정적': '📈',
            '중립적': '➡️',
            '부정적': '📉',
            '매우 부정적': '💥'
        }.get(market_sentiment['sentiment'], '📊')
        
        result = f"{sentiment_emoji} **실시간 시장 분석 ({len(stock_list)}개 종목)**\n\n"
        result += f"🧭 시장 심리: {market_sentiment['sentiment']}\n"
        result += f"📊 상승/하락: {market_sentiment['up_count']}/{market_sentiment['down_count']}\n"
        result += f"📈 평균 변동률: {market_sentiment['avg_change']:+.2f}%\n\n"
        
        result += f"🤖 **AI 시장 분석**: {ai_analysis}\n\n"
        
        result += f"**상위 {min(5, len(stock_list))}개 종목:**\n"
        for stock in top_stocks_info:
            result += f"🏆 {stock['rank']}. **{stock['symbol']}**: {stock['price']:,}원 ({stock['change']:+.2f}%)\n"
        
        if len(stock_list) > 5:
            result += f"\n💡 *총 {len(stock_list)}개 종목 중 상위 5개만 표시*"
        
        return result
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """실제 데이터 기반 요약 처리"""
        try:
            data = input_data.get("data")
            query_type = input_data.get("query_type", "unknown")
            original_query = input_data.get("original_query", "")
            
            if not data:
                return {
                    "status": "error",
                    "message": "요약할 데이터가 없습니다."
                }
            
            # 데이터 타입에 따른 요약
            if isinstance(data, dict):
                # 단일 주식 데이터
                summary = self.format_stock_summary(data, query_type)
            elif isinstance(data, list):
                # 여러 주식 데이터
                summary = self.format_ranking_summary(data, query_type)
            else:
                summary = f"🤖 '{original_query}' 요청을 처리했습니다.\n\n📡 실시간 데이터로 응답했습니다."
            
            return {
                "status": "success",
                "summary": summary,
                "query_type": query_type
            }
            
        except Exception as e:
            self.log_error(f"실제 데이터 요약 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }