
import time
import json
import subprocess
import os
from pathlib import Path
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy


YOUR_USERNAME = ""

APPIUM_SERVER = "http://localhost:4723"
DEVICE_ID = ""

CHECK_INTERVAL = 320  # Check for new DMs every 60 seconds
WAIT_SHORT = 2
WAIT_MEDIUM = 5
WAIT_LONG = 10


class InstagramReelsBot:
    def __init__(self):
        self.driver = None
        self.appium_process = None
        self.processed_reels = self.load_processed_reels()

    def load_processed_reels(self):
        """Load list of already processed reels"""
        try:
            if Path("processed_reels.json").exists():
                with open("processed_reels.json", "r") as f:
                    return set(json.load(f))
        except:
            pass
        return set()

    def save_processed_reels(self):
        """Save list of processed reels"""
        with open("processed_reels.json", "w") as f:
            json.dump(list(self.processed_reels), f)



    def start_appium_server(self):
        """Start Appium server in background"""
        print("[INFO] Checking if Appium is already running...")

        # Check if Appium is already running on port 4723 and kill it
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 4723))
            sock.close()

            if result == 0:
                print("[INFO] Appium is already running on port 4723")
                print("[INFO] Killing existing Appium server to start fresh with correct environment...")
                # Kill any process using port 4723
                subprocess.run(['pkill', '-f', 'appium'], stderr=subprocess.DEVNULL)
                time.sleep(2)  # Wait for process to die
        except Exception:
            pass

        print("[INFO] Starting Appium server...")

        try:
            # Auto-detect Android SDK
            android_sdk = None
            possible_sdk_paths = [
                os.path.expanduser('~/Android/Sdk'),
                os.path.expanduser('~/Library/Android/sdk'),  # macOS
                '/usr/local/android-sdk',
                '/opt/android-sdk',
            ]

            for sdk_path in possible_sdk_paths:
                if os.path.exists(sdk_path):
                    android_sdk = sdk_path
                    print(f"[INFO] Found Android SDK at: {android_sdk}")
                    break

            if not android_sdk:
                print("[WARNING] Could not find Android SDK. Appium may fail to connect.")

            # Source NVM and set Android SDK environment variables, then run appium
            command = f'''
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
            export ANDROID_HOME="{android_sdk}"
            export ANDROID_SDK_ROOT="{android_sdk}"
            appium
            '''

            self.appium_process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                executable='/bin/bash',
                text=True
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
                self.appium_process.terminate()
                self.appium_process.wait(timeout=20)
                print("[SUCCESS] Appium server stopped")
            except:
                try:
                    self.appium_process.kill()
                except:
                    pass

    def connect(self):
        """Connect to Instagram app via Appium"""
        print("[INFO] Connecting to device...")

        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.platform_version = "15"
        options.device_name = "Pixel 9 Pro API 35"
        options.udid = DEVICE_ID
        options.app_package = "com.instagram.android"
        options.app_activity = "com.instagram.mainactivity.MainActivity"
        options.no_reset = True
        options.full_reset = False
        options.new_command_timeout = 300
        options.auto_grant_permissions = True

        # Force app to launch
        options.auto_launch = True
        options.ensure_webviews_have_pages = True

        self.driver = webdriver.Remote(APPIUM_SERVER, options=options)
        self.driver.implicitly_wait(10)

        print("[SUCCESS] Connected to Instagram app!")
        print("[INFO] Launching Instagram...")
        time.sleep(WAIT_LONG)

        # Force activate the app if it's not in foreground
        try:
            self.driver.activate_app("com.instagram.android")
            time.sleep(WAIT_MEDIUM)
        except:
            pass

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

    def navigate_to_dms(self):
        """Navigate to DM inbox"""
        print("[INFO] Opening DMs...")
        try:
            # Look for messenger/DM icon
            dm_selectors = [
                '//android.widget.ImageView[@content-desc="Message"]',
                "//android.widget.Button[@content-desc='Direct']",
                "com.instagram.android:id/direct_tab"
            ]

            for selector in dm_selectors:
                try:
                    if selector.startswith("//"):
                        dm_button = self.driver.find_element(AppiumBy.XPATH, selector)
                    else:
                        dm_button = self.driver.find_element(AppiumBy.ID, selector)
                    dm_button.click()
                    time.sleep(WAIT_SHORT)
                    print("[SUCCESS] Opened DMs")
                    return True
                except:
                    continue

            print("[WARNING] Could not find DM button")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to open DMs: {e}")
            return False

    def find_conversation(self, username):
        """Find and open conversation with specific user"""
        print(f"[INFO] Looking for conversation with @{username}...")
        try:
            # Look for username in conversation list
            conversation_selectors = [
                f"//android.widget.TextView[contains(@text, '{username}')]",
                f"//android.view.View[contains(@content-desc, '{username}')]"
            ]

            for selector in conversation_selectors:
                try:
                    conversation = self.driver.find_element(AppiumBy.XPATH, selector)
                    conversation.click()
                    time.sleep(WAIT_MEDIUM)
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
                time.sleep(WAIT_SHORT)
            except:
                pass

            # Look for message_content FrameLayouts (these contain reels/media)
            reels = []

            try:
                # Primary method: Find by resource-id (most reliable)
                print("[INFO] Looking for message_content elements...")
                message_contents = self.driver.find_elements(
                    AppiumBy.ID,
                    "com.instagram.android:id/message_content"
                )

                if message_contents:
                    print(f"[INFO] Found {len(message_contents)} message_content element(s)")

                    # Filter for media messages (they have larger bounds)
                    for content in message_contents:
                        try:
                            size = content.size
                            location = content.location
                            if size['height'] > 500:  # Media messages are taller
                                print(f"[INFO] Found media element with size: {size}, location: {location}")
                                # Create a unique identifier based on position and size
                                unique_id = f"{location['y']}_{size['height']}_{size['width']}"
                                reels.append({
                                    'element': content,
                                    'id': unique_id
                                })
                        except:
                            continue
                else:
                    print("[WARNING] No message_content elements found")

            except Exception as e:
                print(f"[WARNING] Primary detection failed: {e}")

            # Fallback: Try XPath method
            if not reels:
                print("[INFO] Trying XPath fallback method...")
                try:
                    xpath_reels = self.driver.find_elements(
                        AppiumBy.XPATH,
                        "//android.widget.FrameLayout[@resource-id='com.instagram.android:id/message_content']"
                    )

                    for reel in xpath_reels:
                        try:
                            size = reel.size
                            location = reel.location
                            if size['height'] > 500:
                                unique_id = f"{location['y']}_{size['height']}_{size['width']}"
                                reels.append({
                                    'element': reel,
                                    'id': unique_id
                                })
                        except:
                            continue
                except:
                    pass

            if reels:
                print(f"[SUCCESS] Found {len(reels)} reel(s) to process!")
            else:
                print("[INFO] No reels detected - saving debug info...")
                try:
                    # Save page source to help debug
                    page_source = self.driver.page_source
                    with open("page_source_debug.xml", "w", encoding="utf-8") as f:
                        f.write(page_source)
                    print("[INFO] Page source saved to page_source_debug.xml")
                except:
                    pass

            return reels
        except Exception as e:
            print(f"[ERROR] Failed to check for reels: {e}")
            return []

    def download_reel(self, reel_element):
        """Download reel by saving it"""
        print("[INFO] Downloading reel...")
        try:
            # Click on reel
            # reel_element.click()
            # time.sleep(WAIT_SHORT)

            # Look for more options menu
            # share_selector = "//android.widget.ImageView[@content-desc='Share']"
            #
            # try:
            #     more_button = self.driver.find_element(AppiumBy.XPATH, share_selector)
            #     more_button.click()
            #     time.sleep(WAIT_SHORT)
            # except:
            #     print("[WARNING] Could not find Share button")
            #     return False

            # Look for Save option
            download_selector = "//android.widget.TextView[contains(@text, 'Download')]"

            try:
                save_button = self.driver.find_element(AppiumBy.XPATH, download_selector)
                save_button.click()
                time.sleep(WAIT_MEDIUM)
                print("[SUCCESS] Reel saved!")

            except:
                print("[WARNING] Could not find Download button")
                return False

            while not self.driver.find_element(AppiumBy.XPATH, value='//*[@text="For you"]'):
                # Go back
                self.driver.back()
                time.sleep(WAIT_SHORT)

            return True
        except Exception as e:
            print(f"[ERROR] Failed to download reel: {e}")
            # try:
            #     self.driver.back()
            # except:
            #     pass
            # return False

    def repost_reel(self):
        """Create new reel post from saved video"""
        print("[INFO] Reposting reel...")
        try:

            # Click create button

            post_selector = "com.instagram.android:id/action_bar_buttons_container_left"

            create_btn = self.driver.find_element(AppiumBy.ID, post_selector)
            create_btn.click()
            time.sleep(WAIT_MEDIUM)

            # Select Reel
            select_reel = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,
                                                   'new UiSelector().className("android.view.ViewGroup").instance(2)')
            select_reel.click()
            time.sleep(WAIT_MEDIUM)

            # Click Next multiple times



            next_btn = self.driver.find_element(AppiumBy.ID, "com.instagram.android:id/next_button_textview")
            next_btn.click()
            time.sleep(WAIT_LONG)

            # next_btn_2nd = self.driver.find_element(AppiumBy.ID, "com.instagram.android:id/next_button_textview")
            # next_btn_2nd.click()
            # time.sleep(WAIT_MEDIUM)

            next_btn_3rd = self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Next") or self.driver.find_element(by=AppiumBy.ID, value="com.instagram.android:id/next_button_layout").click()
            next_btn_3rd.click()
            time.sleep(WAIT_MEDIUM)

            # Click Share/Post

            share_btn = self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Share")
            share_btn.click()
            time.sleep(WAIT_LONG)
            print("[SUCCESS] Reel posted!")

        except Exception as e:
            print(f"[ERROR] Failed to repost: {e}")
            self.go_home()
            # Go back to home

    def go_home(self):
        """Navigate to home screen"""
        try:
            home_selectors = [
                "//android.widget.FrameLayout[@content-desc='Home']",
                "//android.widget.Button[@content-desc='Home']"
            ]
            for selector in home_selectors:
                try:
                    home_btn = self.driver.find_element(AppiumBy.XPATH, selector)
                    home_btn.click()
                    time.sleep(WAIT_SHORT)
                    return
                except:
                    continue
        except:
            pass

    def run(self):
        """Main bot loop"""

        try:
            # Start Appium server
            if not self.start_appium_server():
                print("\n[ERROR] Failed to start Appium server. Exiting...")
                print("[INFO] Please ensure Appium is installed:")
                print("       npm install -g appium")
                print("       appium driver install uiautomator2")
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
                    print(f"\n[{time.strftime('%H:%M:%S')}] Checking for new reels...")

                    # Navigate to DMs
                    if not self.navigate_to_dms():
                        print("[WARNING] Could not open DMs, retrying...")
                        continue

                    # Find conversation
                    if not self.find_conversation(YOUR_USERNAME):
                        print(f"[WARNING] No conversation with @{YOUR_USERNAME}, retrying...")
                        continue

                    # Check for reels
                    reels = self.check_for_reels()

                    if reels:

                        for i, reel_data in enumerate(reels):
                            reel_element = reel_data['element']
                            # reel_id = reel_data['id']

                            # Click on reel
                            reel_element.click()
                            time.sleep(WAIT_SHORT)

                            share_selector = "//android.widget.ImageView[@content-desc='Share']"

                            try:
                                more_button = self.driver.find_element(AppiumBy.XPATH, share_selector)
                                more_button.click()
                                time.sleep(WAIT_SHORT)
                            except:
                                print("[WARNING] Could not find Share button")
                                return False

                            # Copy link

                            copy_selector = "//android.widget.ImageView[@content-desc='Copy link']"
                            try:
                                copy_button = self.driver.find_element(AppiumBy.XPATH, copy_selector)
                                copy_button.click()
                                time.sleep(WAIT_SHORT)
                            except:
                                print("[WARNING] Could not find Copy Link button")
                                return False



                            # Get the text from the Android clipboard
                            copied_text = self.driver.get_clipboard_text()
                            print(f"The text I copied was: {copied_text}")

                            reel_id = copied_text



                            if reel_id in self.processed_reels:
                                print(f"[INFO] Reel {i+1} already processed (ID: {reel_id}), skipping...")
                                continue

                            print(f"\n[INFO] Processing reel {i+1}/{len(reels)} (ID: {reel_id})...")

                            # Download
                            if self.download_reel(reel_element):
                                time.sleep(WAIT_MEDIUM)

                                # Repost
                                if self.repost_reel():
                                    print(f"[SUCCESS] Reel reposted!")
                                    self.processed_reels.add(reel_id)
                                    self.save_processed_reels()
                                else:
                                    print(f"[WARNING] Failed to repost")
                                    self.processed_reels.add(reel_id)
                                    self.save_processed_reels()
                            else:
                                print(f"[WARNING] Failed to download")
                                self.processed_reels.add(reel_id)
                                self.save_processed_reels()

                            time.sleep(WAIT_MEDIUM)
                    else:
                        print("[INFO] No new reels found")

                    # Go back to home
                    self.go_home()

                    # Wait before next check
                    print(f"[INFO] Waiting {CHECK_INTERVAL} seconds...")
                    time.sleep(CHECK_INTERVAL)

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"[ERROR] Error in loop: {e}")
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
