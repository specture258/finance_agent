#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from colorama import init, Fore, Style
from dotenv import load_dotenv

load_dotenv()

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from agents.orchestrator import OrchestratorAgent
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("향상된 에이전트 파일들이 있는지 확인해주세요.")
    # 대체로 기본 오케스트레이터 사용 시도
    try:
        from agents.orchestrator import OrchestratorAgent
        OrchestratorAgent = OrchestratorAgent
        print("💡 기본 오케스트레이터를 사용합니다.")
    except ImportError:
        print("agents 디렉토리와 __init__.py 파일들이 있는지 확인해주세요.")
        sys.exit(1)

# 컬러 출력 초기화
init(autoreset=True)

class FinancialAgent:
    def __init__(self):
        self.setup_logging()
        self.orchestrator = OrchestratorAgent()
        self.running = True
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('financial_agent.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def print_welcome(self):
        """환영 메시지 출력"""
        welcome_msg = f"""
{Fore.CYAN}{'='*60}
{Style.BRIGHT}🤖 AI 금융 에이전트에 오신 것을 환영합니다! 🤖
{'='*60}{Style.RESET_ALL}

{Fore.GREEN}💰 주식 정보 조회, 분석, 추천을 도와드립니다.
📊 실시간 데이터와 AI 분석을 통한 투자 인사이트를 제공합니다.

{Fore.YELLOW}📝 사용 예시:
  • "삼성전자 주가 알려줘"
  • "상승률 상위 10개 종목"  
  • "3% 이상 오른 종목 보여줘"
  • "50일 이동평균 돌파 종목"
  • "도움말" (자세한 사용법)

{Fore.RED}⚠️  투자 결정시 신중한 검토가 필요하며, 이 정보는 참고용입니다.

{Fore.CYAN}💡 'exit', 'quit', '종료' 입력시 프로그램이 종료됩니다.
{Style.RESET_ALL}
"""
        print(welcome_msg)
    
    def print_thinking(self):
        """처리 중 표시"""
        print(f"{Fore.YELLOW}🤔 분석 중입니다... 잠시만 기다려주세요.{Style.RESET_ALL}")
    
    def format_response(self, response: str) -> str:
        """응답 포맷팅"""
        # 이모지와 마크다운 스타일 텍스트를 터미널에 맞게 조정
        formatted = response.replace("**", f"{Style.BRIGHT}").replace("*", "")
        
        # 색상 적용
        if "❌" in formatted:
            formatted = f"{Fore.RED}{formatted}{Style.RESET_ALL}"
        elif "🚀" in formatted or "📈" in formatted:
            formatted = f"{Fore.GREEN}{formatted}{Style.RESET_ALL}"
        elif "⚠️" in formatted:
            formatted = f"{Fore.YELLOW}{formatted}{Style.RESET_ALL}"
        else:
            formatted = f"{Fore.CYAN}{formatted}{Style.RESET_ALL}"
        
        return formatted
    
    def get_user_input(self) -> str:
        """사용자 입력 받기"""
        try:
            prompt = f"\n{Fore.MAGENTA}💬 질문을 입력하세요: {Style.RESET_ALL}"
            user_input = input(prompt).strip()
            return user_input
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}👋 프로그램을 종료합니다.{Style.RESET_ALL}")
            return "exit"
        except EOFError:
            return "exit"
    
    def handle_special_commands(self, user_input: str) -> bool:
        """특수 명령어 처리"""
        lower_input = user_input.lower()
        
        # 종료 명령어
        exit_commands = ['exit', 'quit', '종료', 'q']
        if lower_input in exit_commands:
            print(f"\n{Fore.GREEN}👋 이용해 주셔서 감사합니다!{Style.RESET_ALL}")
            return True
        
        # 초기화 명령어
        if lower_input in ['clear', 'reset', '초기화']:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.print_welcome()
            return False
        
        # 상태 명령어
        if lower_input in ['status', '상태']:
            print(f"{Fore.GREEN}✅ 시스템이 정상 작동 중입니다.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 활성 에이전트: DataGatherer, Analyzer, Validator, Summarizer{Style.RESET_ALL}")
            return False
        
        return False
    
    def run(self):
        """메인 실행 루프"""
        self.print_welcome()
        
        while self.running:
            try:
                # 사용자 입력
                user_input = self.get_user_input()
                
                if not user_input:
                    continue
                
                # 특수 명령어 확인
                if self.handle_special_commands(user_input):
                    break
                
                # 처리 중 표시
                self.print_thinking()
                
                # 쿼리 처리
                result = self.orchestrator.process({"query": user_input})
                
                # 결과 출력
                print("\n" + "="*60)
                if result["status"] == "success":
                    formatted_response = self.format_response(result["response"])
                    print(formatted_response)
                else:
                    error_msg = f"{Fore.RED}❌ 오류: {result.get('message', '알 수 없는 오류')}{Style.RESET_ALL}"
                    print(error_msg)
                
                print("="*60)
                
            except Exception as e:
                error_msg = f"{Fore.RED}❌ 시스템 오류: {str(e)}{Style.RESET_ALL}"
                print(error_msg)
                logging.error(f"Main loop error: {str(e)}")

def check_environment():
    """환경 설정 확인"""
    required_env_vars = [
        'KOREA_INVESTMENT_API_KEY',
        'KOREA_INVESTMENT_SECRET_KEY',
        'HYPERCLOVA_API_KEY',
        'HYPERCLOVA_API_GATEWAY_KEY'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"{Fore.RED}❌ 누락된 환경변수가 있습니다:{Style.RESET_ALL}")
        for var in missing_vars:
            print(f"  • {var}")
        print(f"\n{Fore.YELLOW}💡 .env 파일을 생성하여 API 키를 설정해주세요.{Style.RESET_ALL}")
        return False
    
    print(f"{Fore.GREEN}✅ 환경변수 설정이 완료되었습니다.{Style.RESET_ALL}")
    return True

def print_setup_instructions():
    """설정 방법 안내"""
    instructions = f"""
{Fore.CYAN}🔧 설정 방법:{Style.RESET_ALL}

1. 프로젝트 루트 디렉토리에 .env 파일을 생성하세요.

2. 다음 내용을 .env 파일에 추가하세요:
{Fore.YELLOW}
# 한국투자증권 API 키
KOREA_INVESTMENT_API_KEY=your_korea_investment_api_key
KOREA_INVESTMENT_SECRET_KEY=your_korea_investment_secret_key

# 네이버 클라우드 HyperCLOVA API 키
HYPERCLOVA_API_KEY=your_hyperclova_api_key
HYPERCLOVA_API_GATEWAY_KEY=your_hyperclova_gateway_key
{Style.RESET_ALL}

3. API 키 발급 방법:
   • 한국투자증권: https://apiportal.koreainvestment.com/
   • 네이버 클라우드 플랫폼: https://console.ncloud.com/

4. 의존성 설치:
   pip install -r requirements.txt

5. 프로그램 실행:
   python main.py
"""
    print(instructions)

if __name__ == "__main__":
    print(f"{Fore.CYAN}{Style.BRIGHT}🚀 AI 금융 에이전트 시작 중...{Style.RESET_ALL}")
    
    # 환경 설정 확인
    if not check_environment():
        print_setup_instructions()
        sys.exit(1)
    
    try:
        # 앱 시작
        app = FinancialAgent()
        app.run()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 프로그램이 종료되었습니다.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}❌ 시작 중 오류 발생: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)