import os
import sys
import getpass
import robot
from dotenv import load_dotenv
import shutil
import pandas as pd

load_dotenv()


def main():
    print("=========================================")
    print("   Groww RPA Scraper Automation Runner   ")
    print("=========================================")
    
    # Check for command line arguments or prompt interactively
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = os.environ.get("GROWW_EMAIL")
        if not email:
            email = input("Please enter your Groww Email Address: ").strip()
        
    if not email:
        print("Error: Email address cannot be empty.")
        sys.exit(1)
        
    # Collect password from command line arguments or prompt securely
    if len(sys.argv) > 2:
        password = sys.argv[2]
    else:
        password = os.environ.get("GROWW_PASSWORD")
        if not password:
            password = getpass.getpass("Please enter your Groww Password: ").strip()
        
    if not password:
        print("Error: Password cannot be empty.")
        sys.exit(1)
        
    # Collect PIN from command line arguments or prompt securely
    if len(sys.argv) > 3:
        pin = sys.argv[3]
    else:
        pin = os.environ.get("GROWW_PIN")
        if not pin:
            pin = getpass.getpass("Please enter your Groww PIN: ").strip()
        
    if not pin:
        print("Error: PIN cannot be empty.")
        sys.exit(1)
        
    # Dynamically determine paths relative to this script's location
    print("Cleaning existing result directoyr")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    shutil.rmtree(os.path.join(current_dir, "results"))
    base_dir = os.path.dirname(current_dir)  # Navigates up to the 'automation' directory
    robot_file = os.path.join(base_dir, "scraper/login_flow.robot")
    output_dir = os.path.join(base_dir, "scraper/results")
    
    if not os.path.exists(robot_file):
        print(f"Error: The Robot Framework file was not found at expected path: {robot_file}")
        sys.exit(1)
    
    # Pre-create output directory structures
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n[INFO] Starting Robot Framework execution for user: {email}")
    print("[INFO] Spawning live browser view...")
    
    # Run the robot suite programmatically and feed the dynamic EMAIL variable
    exit_code = robot.run(
        robot_file,
        variable=[f"EMAIL:{email}", f"PASSWORD:{password}", f"PIN:{pin}"],
        outputdir=output_dir
    )
    
    if exit_code == 0:
        print("\n[SUCCESS] Phase 1: Login flow completed successfully.")
    else:
        print(f"\n[FAILURE] Automation run failed with exit code: {exit_code}")
        
    sys.exit(exit_code)

def parse_holding_reports():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)
    report_path = os.path.join(base_dir, "scraper/reports")
    data = pd.read_excel(report_path+"/Mutual_Funds_3243591959_25-09-2026_25-09-2026.xlsx")
    data = data.dropna()
    data = data.reset_index(drop=True)
    new_header = data.iloc[0].values
    data.columns = new_header
    final_df = data[1:]
    print(final_df.columns)


if __name__ == "__main__":
    parse_holding_reports()