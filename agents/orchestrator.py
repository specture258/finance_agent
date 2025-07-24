from typing import Dict, Any
from agents.base_agent import BaseAgent
from agents.datagatherer.DataGathererAgent import DataGathererAgent
import re

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("DataOrchestrator")
        
        # 실제 데이터 수집기 사용
        self.data_gatherer = DataGathererAgent()
        
        # 처리 컨텍스트
        self.context = {
            "conversation_history": [],
            "previous_queries": []
        }
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """향상된 쿼리 분석"""
        # 1. 특정 날짜의 주식 가격 조회 (시가, 종가, 고가, 저가)
        price_match = re.search(r'(.+?)의?\s*(\d{4}-\d{2}-\d{2})\s*(시가|종가|고가|저가)(?:은|는)?\?*', query)
        if price_match:
            return {
                "type": "stock_price",
                "symbol": price_match.group(1).strip(),
                "date": price_match.group(2),
                "price_type": price_match.group(3)
            }
        
        # 2. 현재 주가 조회
        current_price_match = re.search(r'(.+?)\s*(?:의?\s*)?(현재가|주가|가격)(?:은|는)?\s*(?:얼마|어떻게)?', query)
        if current_price_match and "날짜" not in query and not re.search(r'\d{4}-\d{2}-\d{2}', query):
            return {
                "type": "stock_price",
                "symbol": current_price_match.group(1).strip()
            }
        
        # 3. 순위 조회 (상승률 상위)
        ranking_match = re.search(r'(상승률|하락률)\s*(상위|하위)\s*(\d+)(?:개)?(?:\s*종목)?', query)
        if ranking_match:
            return {
                "type": "top_gainers" if ranking_match.group(1) == "상승률" else "top_losers",
                "limit": int(ranking_match.group(3))
            }
        
        # 4. 조건부 검색 (% 이상 상승/하락)  
        threshold_match = re.search(r'(\d+(?:\.\d+)?)%\s*이상\s*(상승|하락|오른|떨어진)', query)
        if threshold_match:
            return {
                "type": "above_threshold",
                "threshold": float(threshold_match.group(1)),
                "direction": "up" if threshold_match.group(2) in ["상승", "오른"] else "down"
            }
        
        # 5. 많이 오른 주식
        if "많이" in query and ("오른" in query or "상승" in query):
            return {
                "type": "top_gainers",
                "limit": 10
            }
        
        return {"type": "unknown"}
    
    def get_response(self, analysis: Dict[str, Any], original_query: str) -> str:
        """실제 데이터 기반 응답 생성"""
        try:
            if analysis["type"] == "stock_price":
                return self.handle_stock_price(analysis)
                
            elif analysis["type"] == "top_gainers":
                return self.handle_top_gainers(analysis)
                
            elif analysis["type"] == "above_threshold":
                return self.handle_above_threshold(analysis)
                
            else:
                return f"🤖 '{original_query}' 질문을 이해하지 못했습니다.\n\n💡 다음과 같은 형식으로 질문해보세요:\n• \"삼성전자의 2024-08-08 종가는?\"\n• \"삼성전자 현재가\"\n• \"상승률 상위 5개 종목\"\n• \"3% 이상 상승한 종목\""
        
        except Exception as e:
            return f"❌ 처리 중 오류가 발생했습니다: {str(e)}"
    
    def handle_stock_price(self, analysis: Dict[str, Any]) -> str:
        """주식 가격 조회 처리"""
        symbol = analysis["symbol"]
        date = analysis.get("date")
        price_type = analysis.get("price_type", "current")
        
        # 실제 데이터 조회
        request_data = {
            "type": "stock_price",
            "parameters": {
                "symbol": symbol,
                "date": date,
                "price_type": price_type
            }
        }
        
        result = self.data_gatherer.process(request_data)
        
        if result["status"] == "success":
            data = result["data"]
            
            if "error" in data:
                return f"❌ {data['error']}"
            
            if date and price_type:
                # 특정 날짜, 특정 가격 타입
                price = data.get("price", 0)
                return f"📊 **{symbol}의 {date} {price_type}**\n\n💰 {price:,}원\n\n📡 *실제 시장 데이터 (yfinance)*"
            else:
                # 현재가 조회
                current_price = data.get("current_price", 0)
                change_rate = data.get("change_rate", 0)
                volume = data.get("volume", 0)
                data_source = data.get("data_source", "unknown")
                
                change_emoji = "📈" if change_rate > 0 else "📉" if change_rate < 0 else "➡️"
                
                return f"""{change_emoji} **{symbol} 실시간 현재가**

💰 현재가: {current_price:,}원 ({change_rate:+.2f}%)
📊 거래량: {volume:,}주
🔄 시가: {data.get('open', 0):,}원
📈 고가: {data.get('high', 0):,}원  
📉 저가: {data.get('low', 0):,}원

📡 *데이터 소스: {data_source}*"""
        else:
            return f"❌ 데이터 조회 실패: {result.get('message', '알 수 없는 오류')}"
    
    def handle_top_gainers(self, analysis: Dict[str, Any]) -> str:
        """상승률 상위 종목 처리"""
        limit = analysis.get("limit", 10)
        
        request_data = {
            "type": "top_gainers",
            "parameters": {
                "limit": limit
            }
        }
        
        result = self.data_gatherer.process(request_data)
        
        if result["status"] == "success":
            data = result["data"]
            
            if not data:
                return "❌ 상승률 데이터를 조회할 수 없습니다."
            
            response = f"📈 **실시간 상승률 상위 {len(data)}개 종목**\n\n"
            
            for i, stock in enumerate(data, 1):
                symbol = stock.get("symbol", "")
                price = stock.get("current_price", 0)
                change_rate = stock.get("change_rate", 0)
                volume = stock.get("volume", 0)
                
                response += f"🚀 {i}. **{symbol}**: {price:,}원 ({change_rate:+.2f}%)\n"
                response += f"   └ 거래량: {volume:,}주\n\n"
            
            response += "📡 *실시간 시장 데이터*"
            return response
        else:
            return f"❌ 상승률 데이터 조회 실패: {result.get('message', '알 수 없는 오류')}"
    
    def handle_above_threshold(self, analysis: Dict[str, Any]) -> str:
        """임계값 이상 조회 처리"""
        threshold = analysis.get("threshold", 3.0)
        direction = analysis.get("direction", "up")
        
        request_data = {
            "type": "above_threshold",
            "parameters": {
                "threshold": threshold,
                "direction": direction
            }
        }
        
        result = self.data_gatherer.process(request_data)
        
        if result["status"] == "success":
            data = result["data"]
            
            direction_text = "상승" if direction == "up" else "하락"
            emoji = "📈" if direction == "up" else "📉"
            
            if not data:
                return f"❌ {threshold}% 이상 {direction_text}한 종목이 없습니다."
            
            response = f"{emoji} **실시간 {threshold}% 이상 {direction_text} 종목 ({len(data)}개)**\n\n"
            
            for i, stock in enumerate(data[:15], 1):  # 최대 15개만 표시
                symbol = stock.get("symbol", "")
                price = stock.get("current_price", 0)
                change_rate = stock.get("change_rate", 0)
                
                response += f"🚀 {i}. **{symbol}**: {price:,}원 ({change_rate:+.2f}%)\n"
            
            if len(data) > 15:
                response += f"\n💡 *총 {len(data)}개 종목 중 상위 15개만 표시*\n"
            
            response += "\n📡 *실시간 시장 데이터*"
            return response
        else:
            return f"❌ 조건부 검색 실패: {result.get('message', '알 수 없는 오류')}"
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """메인 처리 (실제 데이터 사용)"""
        try:
            query = input_data.get("query", "").strip()
            
            if not query:
                return {"status": "error", "message": "쿼리가 비어있습니다."}
            
            # 도움말
            if any(word in query.lower() for word in ["도움말", "help", "사용법"]):
                return {
                    "status": "success",
                    "response": """📚 **실시간 AI 금융 에이전트 사용 가이드**

**🔴 실제 시장 데이터 연동 버전**

**✨ 지원하는 질문들:**

1️⃣ **주식 가격 조회**
   • "삼성전자 현재가" (실시간)
   • "삼성전자의 2024-12-01 종가는?" (과거 데이터)
   • "카카오 주가"

2️⃣ **순위 조회**
   • "상승률 상위 10개 종목" (실시간)
   • "상승률 상위 5개 종목"

3️⃣ **조건부 검색**
   • "3% 이상 상승한 종목" (실시간)
   • "5% 이상 오른 주식"
   • "많이 오른 주식"

📡 **데이터 소스:**
• yfinance (글로벌 + 한국 주식)
• 한국투자증권 API (한국 주식 실시간)

⚠️ **주의사항:**
• 실제 시장 데이터를 사용하므로 응답 시간이 약간 소요될 수 있습니다
• 장 마감 시간에는 데이터가 지연될 수 있습니다
• 투자 결정시 신중한 검토가 필요합니다"""
                }
            
            # 쿼리 분석
            analysis = self.analyze_query(query)
            
            # 응답 생성
            response = self.get_response(analysis, query)
            response += "\n\n---\n⚠️ *실제 시장 데이터 기반 - 투자 결정시 신중한 검토 필요*"
            
            return {
                "status": "success", 
                "response": response
            }
            
        except Exception as e:
            self.log_error(f"실제 데이터 오케스트레이터 처리 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }