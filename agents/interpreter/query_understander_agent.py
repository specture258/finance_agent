import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from agents.base_agent import BaseAgent

class QueryUnderstander(BaseAgent):
    def __init__(self):
        super().__init__("QueryUnderstander")
        self.patterns = {
            # 가격 조회 패턴들
            "stock_price_inquiry": [
                r"(.+?)의?\s*(\d{4}-\d{2}-\d{2})\s*(시가|종가|고가|저가)(?:은|는)?\?",
                r"(.+?)\s*(\d{4}-\d{2}-\d{2})\s*(시가|종가|고가|저가)",
                r"(.+?)(?:의)?\s*(현재가|주가|가격)(?:은|는)?\s*(?:얼마|어떻게)?",
            ],
            
            # 시장 통계 패턴들  
            "market_statistics": [
                r"(\d{4}-\d{2}-\d{2})에?\s*(상승|하락)한?\s*종목(?:은|는)?\s*몇\s*개",
                r"(\d{4}-\d{2}-\d{2})\s*(KOSPI|KOSDAQ|코스피|코스닥)?\s*시장에?\s*거래된?\s*종목\s*수",
                r"(\d{4}-\d{2}-\d{2})\s*거래\s*종목\s*수",
            ],
            
            # 순위 조회 패턴들
            "ranking_inquiry": [
                r"(\d{4}-\d{2}-\d{2})(?:에서)?\s*(KOSPI|KOSDAQ|코스피|코스닥)(?:에서)?\s*(상승률|하락률|거래량)\s*(높은|많은)\s*종목\s*(\d+)개",
                r"(상승률|하락률|거래량)\s*(상위|하위)\s*(\d+)(?:개)?(?:\s*종목)?",
                r"(\d{4}-\d{2}-\d{2})\s*가장\s*(많이|적게)\s*(오른|떨어진|거래된)\s*종목",
            ],
            
            # 조건부 검색 패턴들
            "conditional_search": [
                r"(\d+(?:\.\d+)?)%\s*이상\s*(상승|하락|오른|떨어진)",
                r"(\d+(?:\.\d+)?)%\s*(?:이상|초과|이하|미만)",
                r"전날\s*대비\s*(\d+(?:\.\d+)?)%",
            ],
            
            # 시그널 감지 패턴들
            "technical_signal": [
                r"(\d+)일\s*(이동평균|이평선).*?(\d+(?:\.\d+)?)%.*?(돌파|상향|하향)",
                r"이동평균(?:선)?\s*(돌파|상향|하향)",
                r"기술적\s*(돌파|지지|저항)",
            ],
            
            # 특정 날짜 조회
            "date_specific": [
                r"(\d{4}-\d{2}-\d{2})",
                r"(\d{1,2})월\s*(\d{1,2})일",
                r"(오늘|어제|내일)",
            ]
        }
    
    def extract_date(self, text: str) -> Optional[str]:
        """날짜 추출"""
        # YYYY-MM-DD 형식
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if date_match:
            return date_match.group(1)
        
        # MM월 DD일 형식
        month_day_match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', text)
        if month_day_match:
            current_year = datetime.now().year
            month = int(month_day_match.group(1))
            day = int(month_day_match.group(2))
            return f"{current_year}-{month:02d}-{day:02d}"
        
        # 상대적 날짜
        if "오늘" in text:
            return datetime.now().strftime("%Y-%m-%d")
        elif "어제" in text:
            from datetime import timedelta
            yesterday = datetime.now() - timedelta(days=1)
            return yesterday.strftime("%Y-%m-%d")
        
        return None
    
    def extract_stock_name(self, text: str) -> Optional[str]:
        """종목명 추출"""
        # 종목명 패턴들
        patterns = [
            r'([가-힣]+(?:전자|화학|건설|금융|통신|바이오|제약|식품|유통|물산|중공업|그룹|홀딩스|제철|카드|은행|보험|증권|자산|투자|개발|엔지니어링|에너지|소재|머티리얼|테크|시스템|솔루션)(?:우|우선주)?)',
            r'([가-힣]{2,}(?:우|우선주)?)',
            r'(\d{6})',  # 종목코드
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def extract_price_type(self, text: str) -> str:
        """가격 유형 추출 (시가, 종가, 고가, 저가, 현재가)"""
        if "시가" in text:
            return "open"
        elif "종가" in text:
            return "close"  
        elif "고가" in text:
            return "high"
        elif "저가" in text:
            return "low"
        elif "현재가" in text or "주가" in text:
            return "current"
        else:
            return "current"
    
    def extract_market_type(self, text: str) -> str:
        """시장 구분 추출"""
        if "KOSPI" in text or "코스피" in text:
            return "KOSPI"
        elif "KOSDAQ" in text or "코스닥" in text:
            return "KOSDAQ" 
        else:
            return "ALL"
    
    def extract_numbers(self, text: str) -> List[float]:
        """텍스트에서 숫자 추출"""
        return [float(match) for match in re.findall(r'\d+(?:\.\d+)?', text)]
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """향상된 쿼리 이해 및 분류"""
        try:
            query = input_data.get("query", "").strip()
            self.log_info(f"향상된 쿼리 분석 시작: {query}")
            
            result = {
                "original_query": query,
                "query_type": "unknown",
                "parameters": {},
                "confidence": 0.0,
                "sub_type": None
            }
            
            # 1. 가격 조회 분석
            if self._analyze_price_inquiry(query, result):
                pass
            # 2. 시장 통계 분석  
            elif self._analyze_market_statistics(query, result):
                pass
            # 3. 순위 조회 분석
            elif self._analyze_ranking_inquiry(query, result):
                pass
            # 4. 조건부 검색 분석
            elif self._analyze_conditional_search(query, result):
                pass
            # 5. 기술적 시그널 분석
            elif self._analyze_technical_signal(query, result):
                pass
            
            # 공통 파라미터 추가
            self._add_common_parameters(query, result)
            
            self.log_info(f"쿼리 분석 완료: {result['query_type']} (신뢰도: {result['confidence']})")
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            self.log_error(f"향상된 쿼리 이해 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _analyze_price_inquiry(self, query: str, result: Dict[str, Any]) -> bool:
        """가격 조회 분석"""
        for pattern in self.patterns["stock_price_inquiry"]:
            match = re.search(pattern, query)
            if match:
                result["query_type"] = "stock_price_inquiry"
                result["confidence"] = 0.9
                
                if len(match.groups()) >= 3:  # 종목명, 날짜, 가격타입
                    result["parameters"] = {
                        "symbol": match.group(1).strip(),
                        "date": match.group(2),
                        "price_type": self.extract_price_type(match.group(3))
                    }
                    result["sub_type"] = f"historical_{result['parameters']['price_type']}"
                else:
                    result["parameters"] = {
                        "symbol": self.extract_stock_name(query),
                        "price_type": self.extract_price_type(query)
                    }
                    result["sub_type"] = f"current_{result['parameters']['price_type']}"
                
                return True
        return False
    
    def _analyze_market_statistics(self, query: str, result: Dict[str, Any]) -> bool:
        """시장 통계 분석"""
        for pattern in self.patterns["market_statistics"]:
            match = re.search(pattern, query)
            if match:
                result["query_type"] = "market_statistics"
                result["confidence"] = 0.85
                
                if "상승" in query or "하락" in query:
                    result["sub_type"] = "movement_count"
                    result["parameters"] = {
                        "date": match.group(1),
                        "movement": "up" if "상승" in query else "down",
                        "market": self.extract_market_type(query)
                    }
                elif "종목" in query and "수" in query:
                    result["sub_type"] = "total_count"
                    result["parameters"] = {
                        "date": match.group(1),
                        "market": self.extract_market_type(query)
                    }
                
                return True
        return False
    
    def _analyze_ranking_inquiry(self, query: str, result: Dict[str, Any]) -> bool:
        """순위 조회 분석"""
        for pattern in self.patterns["ranking_inquiry"]:
            match = re.search(pattern, query)
            if match:
                result["query_type"] = "ranking_inquiry"
                result["confidence"] = 0.9
                
                numbers = self.extract_numbers(query)
                rank_count = int(numbers[-1]) if numbers else 5
                
                if "상승률" in query:
                    result["sub_type"] = "top_gainers"
                elif "하락률" in query:
                    result["sub_type"] = "top_losers"
                elif "거래량" in query:
                    result["sub_type"] = "top_volume"
                
                result["parameters"] = {
                    "limit": rank_count,
                    "market": self.extract_market_type(query),
                    "date": self.extract_date(query)
                }
                
                return True
        return False
    
    def _analyze_conditional_search(self, query: str, result: Dict[str, Any]) -> bool:
        """조건부 검색 분석"""
        for pattern in self.patterns["conditional_search"]:
            match = re.search(pattern, query)
            if match:
                result["query_type"] = "conditional_search"
                result["confidence"] = 0.85
                
                threshold = float(match.group(1))
                
                if "상승" in query or "오른" in query:
                    result["sub_type"] = "above_threshold"
                    result["parameters"] = {
                        "threshold": threshold,
                        "direction": "up"
                    }
                elif "하락" in query or "떨어진" in query:
                    result["sub_type"] = "below_threshold" 
                    result["parameters"] = {
                        "threshold": threshold,
                        "direction": "down"
                    }
                
                return True
        return False
    
    def _analyze_technical_signal(self, query: str, result: Dict[str, Any]) -> bool:
        """기술적 시그널 분석"""
        for pattern in self.patterns["technical_signal"]:
            match = re.search(pattern, query)
            if match:
                result["query_type"] = "technical_signal"
                result["confidence"] = 0.8
                result["sub_type"] = "moving_average_breakout"
                
                numbers = self.extract_numbers(query)
                ma_days = int(numbers[0]) if numbers else 50
                threshold = numbers[1] if len(numbers) > 1 else 10.0
                
                result["parameters"] = {
                    "ma_period": ma_days,
                    "threshold": threshold,
                    "signal_type": "breakout" if "돌파" in query else "cross"
                }
                
                return True
        return False
    
    def _add_common_parameters(self, query: str, result: Dict[str, Any]):
        """공통 파라미터 추가"""
        # 날짜가 아직 설정되지 않았다면 추출 시도
        if "date" not in result["parameters"]:
            extracted_date = self.extract_date(query)
            if extracted_date:
                result["parameters"]["date"] = extracted_date
        
        # 시장 구분이 설정되지 않았다면 추가
        if "market" not in result["parameters"]:
            result["parameters"]["market"] = self.extract_market_type(query)
        
        # 종목명이 설정되지 않았다면 추가
        if "symbol" not in result["parameters"] and result["query_type"] in ["stock_price_inquiry"]:
            extracted_symbol = self.extract_stock_name(query)
            if extracted_symbol:
                result["parameters"]["symbol"] = extracted_symbol