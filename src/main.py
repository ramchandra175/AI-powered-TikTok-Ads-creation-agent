"""
TikTok Ads AI Agent - Main Entry Point

CLI interface for the conversational ad creation agent
"""

import sys
from colorama import init, Fore, Style

from config import Config
from oauth_manager import TikTokOAuthManager, OAuthError
from api_client import TikTokAPIClient
from agent import TikTokAdsAgent

# Initialize colorama for colored terminal output
init(autoreset=True)


def print_header():
    """Print application header"""
    print("\n" + "=" * 60)
    print(Fore.CYAN + Style.BRIGHT + "TikTok Ads AI Agent")
    print(Fore.CYAN + "Conversational Ad Campaign Creation")
    print("=" * 60 + "\n")


def print_error(message: str):
    """Print error message"""
    print(Fore.RED + "❌ " + message)


def print_success(message: str):
    """Print success message"""
    print(Fore.GREEN + "✅ " + message)


def print_info(message: str):
    """Print info message"""
    print(Fore.BLUE + "ℹ️  " + message)


def setup_oauth(use_mock: bool = False) -> TikTokOAuthManager:
    """Setup OAuth authentication"""
    oauth_manager = TikTokOAuthManager(use_mock=use_mock)
    
    # Check if we already have valid token
    if oauth_manager.has_valid_token():
        print_success("Using existing access token")
        return oauth_manager
    
    print_info("OAuth authentication required")
    
    if use_mock:
        # Mock OAuth
        print_info("Using mock OAuth (testing mode)")
        oauth_manager.start_oauth_flow()
        print_success("Mock authentication completed")
    else:
        # Real OAuth flow
        print("\nStarting OAuth flow...")
        print("1. A browser window will open")
        print("2. Log in to TikTok and authorize the app")
        print("3. You'll be redirected back to complete authentication\n")
        
        try:
            # Get authorization URL
            auth_url = oauth_manager.start_oauth_flow()
            print(f"Authorization URL: {auth_url}")
            print("\nPlease visit this URL to authorize the app.")
            
            # In production, would use callback server
            code = input("\nEnter the authorization code from the redirect: ")
            
            # Exchange code for token
            oauth_manager.exchange_code_for_token(code)
            print_success("OAuth authentication completed")
            
        except OAuthError as e:
            print_error(f"OAuth failed: {e.message}")
            if e.suggestion:
                print_info(f"Suggestion: {e.suggestion}")
            sys.exit(1)
    
    return oauth_manager


def main():
    """Main application entry point"""
    print_header()
    
    # Load configuration
    Config.print_config()
    
    # Validate configuration
    errors = Config.validate()
    if errors and not Config.USE_MOCK_API:
        print_error("Configuration errors:")
        for error in errors:
            print(f"  • {error}")
        print_info("Please update your .env file or set USE_MOCK_API=true")
        sys.exit(1)
    
    use_mock = Config.USE_MOCK_API
    
    # Setup OAuth
    try:
        oauth_manager = setup_oauth(use_mock)
    except Exception as e:
        print_error(f"Authentication failed: {str(e)}")
        sys.exit(1)
    
    # Initialize API client
    api_client = TikTokAPIClient(oauth_manager, use_mock=use_mock)
    
    # Initialize agent
    agent = TikTokAdsAgent(oauth_manager, api_client, use_mock=use_mock)
    
    print("\n" + "=" * 60)
    print(Fore.GREEN + Style.BRIGHT + "Agent Ready!")
    print("=" * 60)
    print("\nI'll help you create a TikTok ad campaign.")
    print("Just chat with me naturally, and I'll guide you through the process.\n")
    print(Fore.YELLOW + "Type 'quit' or 'exit' to end the conversation")
    print(Fore.YELLOW + "Type 'summary' to see current campaign data")
    print(Fore.YELLOW + "Type 'reset' to start a new campaign\n")
    
    # Start conversation
    try:
        response = agent.start_conversation()
        print(Fore.CYAN + f"\nAgent: {response}\n")
        
        # Main conversation loop
        while True:
            try:
                user_input = input(Fore.WHITE + "You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit']:
                    print(Fore.YELLOW + "\nGoodbye! 👋\n")
                    break
                
                elif user_input.lower() == 'summary':
                    print(Fore.MAGENTA + "\n" + agent.get_campaign_summary() + "\n")
                    continue
                
                elif user_input.lower() == 'reset':
                    agent.reset()
                    print_success("Campaign data reset. Starting fresh!\n")
                    response = agent.start_conversation()
                    print(Fore.CYAN + f"\nAgent: {response}\n")
                    continue
                
                # Process user input
                response = agent.process_user_input(user_input)
                print(Fore.CYAN + f"\nAgent: {response}\n")
                
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\nInterrupted. Type 'quit' to exit.\n")
                continue
    
    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        if Config.DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()