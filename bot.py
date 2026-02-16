import re
import time
import subprocess
import os
import platform
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy


YOUR_USERNAME = ""

APPIUM_SERVER = "http://localhost:4723"
DEVICE_ID = ""

CHECK_INTERVAL = 320  # Check for new DMs every 320 seconds

class InstagramReelsBot:
    def __init__(self):
        self.driver = None
        self.appium_process = None

    def load_processed_reels(self, id):
        """Load list of already processed reels"""
        if not os.path.exists('processed_reels.txt'):
            # in case the file does not exist, we will create it
            with open('processed_reels.txt', 'w') as f:
                pass
            return True

        with open('processed_reels.txt', 'r') as file:
            content = file.read()
            if id in content:
                print(f"[INFO] Reel {id} already processed, skipping...")
                print(f"Checking again after {CHECK_INTERVAL} seconds...")
                return False
            else:
                return True

    def save_processed_reels(self, id):
        """Save list of processed reels"""
        with open('processed_reels.txt', 'a') as file:
            file.write(f"\n{id}")


    def start_appium_server(self):
        """Start Appium server in background, with OS-specific handling."""
        print("[INFO] Checking if Appium is already running...")
        current_os = platform.system()

        # Check if Appium is already running on port 4723 and kill it
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 4723))
            sock.close()

            if result == 0:
                print("[INFO] Appium is already running on port 4723")
                print("[INFO] Killing existing Appium server to start fresh with correct environment...")
                if current_os == "Windows":
                    subprocess.run(['taskkill', '/F', '/IM', 'node.exe'], stderr=subprocess.DEVNULL)
                else:  # macOS and Linux
                    subprocess.run(['pkill', '-f', 'appium'], stderr=subprocess.DEVNULL)
                time.sleep(2)  # Wait for process to die
        except Exception as e:
            print(f"[WARNING] Failed to check or kill existing Appium process: {e}")

        print("[INFO] Starting Appium server...")

        try:
            # Auto-detect Android SDK
            android_sdk = None
            possible_sdk_paths = []
            if current_os == "Windows":
                possible_sdk_paths = [
                    os.path.join(os.environ.get("LOCALAPPDATA"), "Android", "Sdk"),
                    os.path.join(os.environ.get("ProgramFiles"), "Android", "android-sdk"),
                ]
            else:  # macOS and Linux
                possible_sdk_paths = [
                    os.path.expanduser('~/Android/Sdk'),
                    os.path.expanduser('~/Library/Android/sdk'),  # macOS
                    '/usr/local/android-sdk',
                    '/opt/android-sdk',
                ]

            for sdk_path in possible_sdk_paths:
                if sdk_path and os.path.exists(sdk_path):
                    android_sdk = sdk_path
                    print(f"[INFO] Found Android SDK at: {android_sdk}")
                    break

            if not android_sdk:
                print("[WARNING] Could not find Android SDK. Appium may fail to connect.")
                android_sdk = ""

            # Set environment variables and run Appium
            env = os.environ.copy()
            env['ANDROID_HOME'] = android_sdk
            env['ANDROID_SDK_ROOT'] = android_sdk

            command = []
            shell = False
            executable = None

            if current_os == "Windows":
                command = ['appium']
                shell = True
            else:
                command = f'''
                export NVM_DIR="$HOME/.nvm"
                [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
                appium
                '''
                shell = True
                executable = '/bin/bash'

            self.appium_process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                executable=executable,
                text=True,
                env=env
            )

            # Give Appium a few seconds to start and check output
            print("[INFO] Waiting for Appium to start...")
            time.sleep(5)

            # Check if process is still running
            if self.appium_process.poll() is not None:
                # Process died, show the output
                output = self.appium_process.stdout.read()
                print("[ERROR] Appium failed to start")
                print("[ERROR] Output:")
                print(output)
                return False

            print("[SUCCESS] Appium server started")
            return True

        except FileNotFoundError:
            print("[ERROR] Appium not found. Please install it:")
            print("        npm install -g appium")
            print("        appium driver install uiautomator2")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to start Appium: {e}")
            return False

    def stop_appium_server(self):
        """Stop Appium server"""
        if self.appium_process:
            print("[INFO] Stopping Appium server...")
            try:
                if platform.system() == "Windows":
                    # On Windows, terminate doesn't kill child processes (like node)
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.appium_process.pid)], stderr=subprocess.DEVNULL)
                else:
                    self.appium_process.terminate()
                    self.appium_process.wait(timeout=20)
                print("[SUCCESS] Appium server stopped")
            except Exception as e:
                print(f"[WARNING] Could not terminate Appium gracefully: {e}. Killing...")
                try:
                    self.appium_process.kill()
                except Exception as kill_e:
                    print(f"[ERROR] Failed to kill Appium process: {kill_e}")

    def connect(self):
        """Connect to Instagram app via Appium"""
        print("[INFO] Connecting to device...")

        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.udid = DEVICE_ID
        options.app_package = "com.instagram.android"
        options.app_activity = "com.instagram.android.activity.MainTabActivity"
        options.no_reset = True
        options.full_reset = False
        options.new_command_timeout = 600
        options.auto_grant_permissions = True

        # Force app to launch
        options.auto_launch = True
        options.ensure_webviews_have_pages = True

        self.driver = webdriver.Remote(APPIUM_SERVER, options=options)
        self.driver.implicitly_wait(10)

        print("[SUCCESS] Connected to Instagram app!")
        print("[INFO] Launching Instagram...")
        time.sleep(5)

        # Force activate the app if it's not in foreground
        try:
            self.driver.activate_app("com.instagram.android")
            time.sleep(5)
        except:
            pass

        # Handle any initial pop-ups after launch
        self.handle_popups()

    def is_logged_in(self):
        """Check if already logged in"""
        try:
            # Look for home screen elements
            home_indicators = [
                "//android.widget.FrameLayout[@content-desc='Home']",
                "com.instagram.android:id/tab_bar"
            ]
            for selector in home_indicators:
                try:
                    if selector.startswith("//"):
                        self.driver.find_element(AppiumBy.XPATH, selector)
                    else:
                        self.driver.find_element(AppiumBy.ID, selector)
                    print("[INFO] Already logged in!")
                    return True
                except:
                    continue
        except:
            pass
        return False

    def check_connection_health(self):
        try:
            current_activity = self.driver.current_activity
            if current_activity:
                return True
        except Exception as e:
            print(f"[WARNING] Connection health check failed: {e}")
            return False
        return False

    def handle_popups(self):
        """Handle common pop-ups by clicking 'Not now' or similar buttons."""
        print("[INFO] Checking for pop-ups...")


        popup_selectors = [
            (AppiumBy.ACCESSIBILITY_ID, "Not now"),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("OK")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Got it")'),
            (AppiumBy.ID, "com.instagram.android:id/appirater_cancel_button"),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("No, thanks")')
        ]

        for by, selector in popup_selectors:
            try:
                element = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((by, selector)))
                element.click()
                print(f"[SUCCESS] Dismissed popup using: {selector}")
                time.sleep(1)
            except:
                continue

        try:
            if len(self.driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR,
                                             'new UiSelector().text("Get more from your next reel")')) > 0:
                self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("For you")').click()
        except:
            pass

    def navigate_to_dms(self):
        """Navigate to DM inbox"""
        print("[INFO] Opening DMs...")
        try:
            # Look for messenger/DM icon
            dm_button = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((AppiumBy.ID, "com.instagram.android:id/direct_tab")))
            dm_button.click()
            print("[SUCCESS] Opened DMs")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to open DMs: {e}")
            return False

    def find_conversation(self, username):
        """Find and open conversation with specific user"""
        print(f"[INFO] Looking for conversation with @{username}...")
        try:
            # Look for username in conversation list
            conversation_selectors = [
                f"new UiSelector().text('{username}')",
                f'new UiSelector().resourceId("com.instagram.android:id/row_inbox_username")'
            ]

            for selector in conversation_selectors:
                try:
                    conversation = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, selector)
                    conversation.click()
                    print(f"[SUCCESS] Opened conversation with @{username}")
                    return True
                except:
                    continue

            print(f"[WARNING] No conversation found with @{username}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to find conversation: {e}")
            return False

    def check_for_reels(self):
        print("[INFO] Checking for reels...")
        try:
            # Scroll up to load more messages
            print("[INFO] Scrolling to load messages...")
            try:
                self.driver.swipe(500, 1000, 500, 500, 500)
            except:
                pass

            # Look for message_content FrameLayouts (these contain reels/media)
            try:
                print("[INFO] Looking for message_content elements...")
                # 1. Wait for all elements to be present
                reels = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (AppiumBy.ID, "com.instagram.android:id/message_content_horizontal_placeholder_container"))
                )

                # 2. Pick the last one (highest instance)
                reel = reels[-1]
                reel.click()

                share_button = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("com.instagram.android:id/direct_share_button")')))
                share_button.click()

                reel_link = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Copy link")')))
                reel_link.click()
                time.sleep(1)
                unique_id = self.driver.get_clipboard_text()
                unique_id = re.search(r"\/reels?\/([^\/\?#]+)", unique_id)

                if unique_id:
                    unique_id = unique_id.group(1)
                else:
                    # If it fails, unique_id stays as the full URL or you can set a fallback
                    print("Warning: Regex could not find the ID in the string.")

                if self.load_processed_reels(unique_id):
                    # Add to processed reels and save
                    self.save_processed_reels(unique_id)
                else:
                    return False

                print(f"[SUCCESS] Found new reel with ID: {unique_id}")
                return True


            except Exception as e:
                print(f"[ERROR] Failed to process reel: {e}")
                return None

        except Exception as e:
            print(f"[ERROR] Failed to check for reels: {e}")
            return None



    def download_reel(self):
        """Download reel by saving it"""
        print("[INFO] Downloading reel...")

        try:
            save_button = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Download")')))
            save_button.click()
            time.sleep(10)
            print("[SUCCESS] Reel saved!")

        except:
            print("[WARNING] Could not find Download button")
            return False

        return True

    def go_home(self):
        """Navigate to home screen"""
        selector = 'new UiSelector().resourceId("com.instagram.android:id/title_text").text("For you")'
        attempts = 0
        max_attempts = 7

        while len(self.driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, value=selector)) == 0:
            if attempts >= max_attempts:
                print("[WARNING] Could not reach Home screen after multiple attempts. Restarting app...")
                self.driver.activate_app("com.instagram.android")
                time.sleep(2)
                break

            self.driver.back()
            time.sleep(2)
            attempts += 1

    def clear_stored_videos(self):
        """Deletes downloaded video files from the specific internal storage path"""
        print("[INFO] Clearing video files from emulator memory...")
        try:
            target_path = "/storage/emulated/0/Movies/Instagram/*"

            command = f"adb shell rm -f {target_path}"

            subprocess.run(command.split(), stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            print(f"[SUCCESS] Cleared files from {target_path}")
        except Exception as e:
            print(f"[WARNING] Could not clear files: {e}")

    def repost_reel(self):
        """Create new reel post from saved video"""
        print("[INFO] Reposting reel...")
        try:
            # Click create button - try multiple strategies with the exact attributes you provided
            create_btn = None
            strategies = [
                '//android.widget.LinearLayout[@resource-id="com.instagram.android:id/action_bar_buttons_container_left"]/android.widget.ImageView',
                'new UiSelector().resourceId("com.instagram.android:id/action_bar_buttons_container_left").childSelector(new UiSelector().className("android.widget.ImageView").clickable(true))',
                'new UiSelector().className("android.widget.ImageView").bounds(0, 63, 127, 210)',
            ]
            
            for strategy in strategies:
                try:
                    if strategy.startswith('//'):
                        # XPath strategy
                        create_btn = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((AppiumBy.XPATH, strategy)))
                    else:
                        # UiAutomator strategy
                        create_btn = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, strategy)))
                    
                    if create_btn:
                        print(f"[SUCCESS] Found create button using: {strategy}")
                        break
                except Exception as find_error:
                    print(f"[DEBUG] Strategy failed: {strategy} - {str(find_error)[:100]}")
                    continue
            
            if not create_btn:
                raise Exception("Could not find create button with any strategy. Please check if Instagram layout has changed.")
            create_btn.click()

            # Select Reel
            select_reel = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR,
                                                'new UiSelector().resourceId("com.instagram.android:id/background_color").instance(0)')))
            select_reel.click()

            # Click Next multiple times
            next_btn = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((AppiumBy.ID, "com.instagram.android:id/next_button_textview")))
            next_btn.click()

            # Second Next button
            next_btn_2nd = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (AppiumBy.ANDROID_UIAUTOMATOR,
                 'new UiSelector().resourceId("com.instagram.android:id/clips_right_action_button")')))
            next_btn_2nd.click()


            print("[INFO] Adding caption...")
            try:
                caption_text = (
                    "#🇯🇵Japan is turning footsteps into electricity! "
                    "Using piezoelectric tiles, every step you take generates a small amount of energy. "
                    "Millions of steps together can power LED lights and displays in busy places like Shibuya Station. "
                    "A brilliant way to create a sustainable and smart city turning m..."
                    "兄弟，他真觉得自己在那份爱泼斯坦名单上💀 "
                    "特朗普刚才那记总统级魅力（Rizz）直接给哥们整不会了，吹牛老爹（Diddy）还在旁边 4K 高清观看。 "
                    "这波负面气场（Aura）简直比内塔尼亚胡在新闻发布会上还重。 "
                    "这波到底是系统 Bug 还是代码飞升？👇 \n"
                    ". \n"
                    "#气场 #魅力 #特朗普 #吹牛老爹 #脑干缺失 #短视频 #流量密码 #系统漏洞 #fyp"
                )

                caption_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((AppiumBy.ID, "com.instagram.android:id/caption_input_text_view")))
                caption_field.click()
                time.sleep(1)
                caption_field.send_keys(caption_text)
                print("[SUCCESS] Caption added.")
            except Exception as e:
                print(f"[ERROR] Could not add caption: {e}")

            self.driver.hide_keyboard()

            try:
                popup_share = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Update on your original audio")')))
                popup_share.click()
                if self.driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().resourceId("com.instagram.android:id/row_pending_media_status_textview").text("Done posting. Want to send it directly to friends?")'):
                    print("[SUCCESS] Reel posted!")
            except:
                print("Popup share not found, continuing with normal Share button.")
                share_btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Share")')))
                share_btn.click()
                if WebDriverWait(self.driver, 15).until(EC.presence_of_all_elements_located((AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().resourceId("com.instagram.android:id/row_pending_media_status_textview").text("Done posting. Want to send it directly to friends?")'))):
                    print("[SUCCESS] Reel posted!")

        except Exception as e:
            print(f"[ERROR] Failed to repost: {e}")
            self.go_home()

    def run(self):
        """Main bot loop"""

        try:
            # Start Appium server
            if not self.start_appium_server():
                print("\n[ERROR] Failed to start Appium server. Exiting...")
                print("[INFO] Please ensure Appium is installed:")
                return

            # Connect to device
            self.connect()

            # Check if logged in
            if not self.is_logged_in():
                print("[WARNING] Not logged in! Please log in manually on the device.")
                print("[INFO] Waiting 60 seconds for you to log in...")
                time.sleep(60)

                # Check again after waiting
                if not self.is_logged_in():
                    print("[ERROR] Still not logged in. Please log in and restart the bot.")
                    return

            print("\n[INFO] Starting monitoring loop...")
            print(f"[INFO] Checking every {CHECK_INTERVAL} seconds")
            print("[INFO] Press Ctrl+C to stop\n")

            while True:
                try:
                    # Check connection health before proceeding
                    if not self.check_connection_health():
                        print("[WARNING] Connection lost. Attempting to reconnect...")
                        
                        # Try to reconnect
                        try:
                            if self.driver:
                                self.driver.quit()
                                time.sleep(5)
                            self.connect()
                            print("[SUCCESS] Reconnected to device")
                        except Exception as reconnect_error:
                            print(f"[ERROR] Failed to reconnect: {reconnect_error}")
                            print("[INFO] Attempting Appium server restart...")
                            
                            # Restart Appium server as last resort
                            self.stop_appium_server()
                            time.sleep(5)
                            if not self.start_appium_server():
                                print("[ERROR] Failed to restart Appium server. Stopping bot.")
                                break
                            
                            # Try connecting again
                            self.connect()
                            print("[SUCCESS] Reconnected after Appium restart")
                        
                        # Continue to next iteration after reconnection
                        continue
                    
                    self.clear_stored_videos()
                    print(f"\n[{time.strftime('%H:%M:%S')}] Checking for new reels...")

                    self.go_home()
                    # Navigate to DMs
                    if not self.navigate_to_dms():
                        print("[WARNING] Could not open DMs, retrying...")
                        self.handle_popups() # Check for popups on home screen
                        continue

                    self.handle_popups()  # Handle pop-ups after navigating

                    # Find conversation
                    if not self.find_conversation(YOUR_USERNAME):
                        print(f"[WARNING] No conversation with @{YOUR_USERNAME}, retrying...")
                        self.handle_popups()
                        continue

                    self.handle_popups() # Handle pop-ups in conversation

                    # Check for reels
                    if not self.check_for_reels():
                        print(f"[INFO] No new reels found, retrying in {CHECK_INTERVAL} seconds...")
                        time.sleep(CHECK_INTERVAL)
                        continue
                    # Download
                    if not self.download_reel():
                        print(f"[INFO] This reel doesn't have a download button, retrying in {CHECK_INTERVAL} seconds...")
                        time.sleep(CHECK_INTERVAL)
                        continue

                    self.go_home()

                    self.handle_popups() # Handle pop-ups after download

                    # Repost
                    self.repost_reel()

                    self.handle_popups() # Final check before next reel

                    # Go back to home
                    self.go_home()
                    self.handle_popups() # Final check on home screen

                    # Wait before next check
                    print(f"[INFO] Waiting {CHECK_INTERVAL} seconds...")
                    time.sleep(CHECK_INTERVAL)

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"[ERROR] Error in loop: {e}")
                    
                    # Handle UiAutomator2 instrumentation crashes
                    if "instrumentation process is not running" in str(e) or "UiAutomator2" in str(e):
                        print("[ERROR] Appium UiAutomator2 server crashed. Attempting recovery...")
                        
                        # Try to restart Appium server
                        print("[INFO] Restarting Appium server...")
                        self.stop_appium_server()
                        time.sleep(5)
                        
                        if not self.start_appium_server():
                            print("[ERROR] Failed to restart Appium server. Stopping bot.")
                            break
                        
                        # Reconnect to device
                        print("[INFO] Reconnecting to device...")
                        try:
                            if self.driver:
                                self.driver.quit()
                                time.sleep(3)
                            self.connect()
                            print("[SUCCESS] Reconnected to device")
                        except Exception as reconnect_error:
                            print(f"[ERROR] Failed to reconnect: {reconnect_error}")
                            print("[INFO] Will retry full restart in 60 seconds...")
                            time.sleep(60)
                            continue
                    
                    else:
                        # Log specific error details for debugging
                        if "cannot be proxied to UiAutomator2 server" in str(e):
                            print("[ERROR] UiAutomator2 server communication failed. This usually means:")
                            print("        - Appium server crashed")
                            print("        - Android instrumentation process died")
                            print("        - Device connection was lost")
                            print("[INFO] Recovery procedures will be attempted on next iteration")
                        
                        print("[INFO] Retrying in 30 seconds...")
                        time.sleep(30)

        except KeyboardInterrupt:
            print("\n\n[INFO] Stopping bot...")
        finally:
            if self.driver:
                self.driver.quit()
            # Stop Appium server
            self.stop_appium_server()
            print("[INFO] Bot stopped. Goodbye!")

if __name__ == "__main__":
    print("=" * 50)
    print("Instagram Reels Reposter Bot")
    print("=" * 50)
    print(f"Monitoring DMs from: @{YOUR_USERNAME}")
    print(f"Device: {DEVICE_ID}")
    print("=" * 50)

    bot = InstagramReelsBot()
    bot.run()