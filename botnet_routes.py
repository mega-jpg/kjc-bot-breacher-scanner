from fastapi import APIRouter, HTTPException
from typing import Dict
from botnet_service import get_botnet_service

router = APIRouter()

@router.post("/botnet")
async def botnet(request: Dict):
    """🤖 Single bot login using optimized botnet service"""
    botnet_service = get_botnet_service()
    username = request.get("username", "")
    password = request.get("password", "")
    appId = request.get("appId", "")
    result = await botnet_service.manage_bot_session(username, password, appId)
    if result.get("success"):
        return {
            "message": result["message"],
            "username": result["username"],
            "userId": result.get("userId", ""),
            "accessToken": result.get("accessToken", ""),
            "authCode": result.get("authCode", ""),
            "sync_result": result.get("sync_result", {}),
            "ws_result": result.get("ws_result", {}),
            "ws_response": result.get("ws_result", {}).get("response", ""),
        }
    else:
        return {"message": result.get("message", "Unknown error"), "success": False}

@router.post("/scrape-sjc")
async def scrape_sjc(request: Dict):
    """💳 Filter and validate credit cards from CSV data using Luhn algorithm & BIN lookup"""
    try:
        botnet_service = get_botnet_service()
        csv_data = request.get("csv_data", None)
        result = await botnet_service.scrape_sjc(csv_data=csv_data)
        if result.get("success"):
            return {
                "message": "Card filtering completed successfully",
                "status": "success",
                "data": result
            }
        else:
            return {
                "message": f"Card filtering failed: {result.get('error', 'Unknown error')}",
                "status": "error",
                "data": result
            }
    except Exception as e:
        return {
            "message": f"API error: {str(e)}",
            "status": "error"
        }

@router.post("/generate-utility-bills")
async def generate_utility_bills(request: Dict):
    """💡 Generate fake utility bills with images using passport data from Docs folder"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import random
        from datetime import datetime, timedelta
        import os
        import json
        
        # Get count from request
        count = request.get("count", 10)
        if count > 100:
            count = 100  # Limit to 100 bills
        
        # Create output directory if not exists
        output_dir = "static/UtilityBill"
        os.makedirs(output_dir, exist_ok=True)
        
        # Read passport data from Docs folder
        passports_file = "static/Docs/passports_index.json"
        passports_data = []
        
        if os.path.exists(passports_file):
            with open(passports_file, "r", encoding="utf-8") as f:
                passports_data = json.load(f)
        
        # If no passport data exists, return error
        if not passports_data:
            return {
                "status": "error",
                "message": "No passport data found. Please generate documents first using the Document Generator tab."
            }
        
        # Limit count to available passports
        count = min(count, len(passports_data))
        
        companies = ["British Gas", "EDF Energy", "Scottish Power", "E.ON", "npower"]
        
        bills = []
        
        for i in range(count):
            # Use passport data instead of random generation
            passport = passports_data[i]
            full_name = passport["name"]
            address = passport["address"]
            
            # Generate random amount and date
            amount = random.uniform(45.67, 289.34)
            days_ago = random.randint(0, 90)
            bill_date = (datetime.now() - timedelta(days=days_ago)).strftime("%d/%m/%Y")
            
            company = random.choice(companies)
            
            # Create image (600x800 utility bill template)
            img = Image.new('RGB', (600, 800), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                font_title = ImageFont.truetype("arial.ttf", 32)
                font_bold = ImageFont.truetype("arialbd.ttf", 24)
                font_regular = ImageFont.truetype("arial.ttf", 20)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                font_title = ImageFont.load_default()
                font_bold = ImageFont.load_default()
                font_regular = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw utility bill template
            # Header
            draw.rectangle([(0, 0), (600, 80)], fill='#1e3a8a')
            draw.text((50, 25), company, fill="white", font=font_title)
            
            # Bill details
            y_offset = 120
            draw.text((50, y_offset), "UTILITY BILL", fill="#1e3a8a", font=font_bold)
            
            y_offset += 60
            draw.text((50, y_offset), "Bill To:", fill="black", font=font_bold)
            y_offset += 35
            draw.text((50, y_offset), full_name, fill="black", font=font_regular)
            y_offset += 30
            draw.text((50, y_offset), address, fill="black", font=font_small)
            
            y_offset += 80
            draw.rectangle([(50, y_offset), (550, y_offset + 2)], fill='#d1d5db')
            
            y_offset += 30
            draw.text((50, y_offset), "Bill Date:", fill="black", font=font_bold)
            draw.text((350, y_offset), bill_date, fill="black", font=font_regular)
            
            y_offset += 80
            draw.text((50, y_offset), "Amount Due:", fill="black", font=font_bold)
            draw.text((350, y_offset), f"${amount:.2f}", fill="#dc2626", font=font_bold)
            
            y_offset += 80
            draw.rectangle([(50, y_offset), (550, y_offset + 2)], fill='#d1d5db')
            
            y_offset += 30
            draw.text((50, y_offset), "Account Number: " + str(random.randint(100000000, 999999999)), fill="#6b7280", font=font_small)
            y_offset += 25
            draw.text((50, y_offset), "Reference: " + str(random.randint(1000000, 9999999)), fill="#6b7280", font=font_small)
            
            # Footer
            draw.rectangle([(0, 720), (600, 800)], fill='#f3f4f6')
            draw.text((50, 750), "Thank you for your payment", fill="#6b7280", font=font_small)
            
            # Save image
            filename = f"utility_{random.randint(100000, 999999)}.png"
            filepath = os.path.join(output_dir, filename)
            img.save(filepath)
            
            bills.append({
                "filename": filename,
                "name": full_name,
                "address": address,
                "amount": amount,
                "date": bill_date,
                "company": company
            })
        
        return {
            "status": "success",
            "message": f"Successfully generated {len(bills)} utility bills using passport data",
            "data": {
                "bills": bills,
                "count": len(bills),
                "output_folder": output_dir,
                "source": "Passport data from static/Docs/passports_index.json"
            }
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Error generating utility bills: {str(e)}",
            "traceback": traceback.format_exc()
        }

@router.post("/generate-passports")
async def generate_passports(request: Dict):
    """🛂 Generate fake UK passports with hologram, UV layer, and MRZ from individual JSON files"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import random
        from datetime import datetime, timedelta
        import os
        import json
        import glob
        
        # Get count from request
        count = request.get("count", 10)
        if count > 100:
            count = 100  # Limit to 100 passports
        
        # Create output directory if not exists
        output_dir = "static/UKPassport"
        os.makedirs(output_dir, exist_ok=True)
        
        # Read all individual JSON files from Docs folder
        docs_dir = "static/Docs"
        json_files = glob.glob(os.path.join(docs_dir, "*.json"))
        
        # Filter out index file, only get individual passport files
        json_files = [f for f in json_files if not f.endswith("passports_index.json")]
        
        # If no passport data exists, return error
        if not json_files:
            return {
                "status": "error",
                "message": "No passport data found. Please generate documents first using the Document Generator tab."
            }
        
        # Limit count to available passport files
        count = min(count, len(json_files))
        
        # Read data from individual JSON files
        passports_data = []
        selected_files = random.sample(json_files, count) if len(json_files) > count else json_files
        
        for json_file in selected_files:
            with open(json_file, "r", encoding="utf-8") as f:
                passport_data = json.load(f)
                passports_data.append(passport_data)
        
        passports = []
        
        for i in range(count):
            # Use passport data
            passport_data = passports_data[i]
            full_name = passport_data["name"]
            dob_text = passport_data["dob"]  # "15 March 1985"
            
            # Generate UK passport number
            passport_no = f"GB{random.randint(100000000, 999999999)}"
            
            # Create base image (850x550 - UK passport size)
            bg = Image.new('RGB', (850, 550), color='#8B0000')  # Dark red background
            draw = ImageDraw.Draw(bg)
            
            # Layer 1: Background pattern
            for x in range(0, 850, 30):
                for y in range(0, 550, 30):
                    draw.ellipse([(x, y), (x+10, y+10)], fill=(139, 10, 10, 50))
            
            # Layer 2: Hologram effect (random "UNITED KINGDOM" text overlay)
            holo = Image.new('RGBA', bg.size, (0, 0, 0, 0))
            h_draw = ImageDraw.Draw(holo)
            
            try:
                font_holo = ImageFont.truetype("arial.ttf", 40)
            except:
                font_holo = ImageFont.load_default()
            
            for _ in range(80):
                x = random.randint(0, 800)
                y = random.randint(0, 500)
                alpha = random.randint(10, 30)
                h_draw.text((x, y), "UK", fill=(255, 255, 255, alpha), font=font_holo)
            
            # Layer 3: UV effect (purple tint)
            uv = Image.new('RGBA', bg.size, (138, 43, 226, 20))
            
            # Layer 4: Main content area (white rectangle)
            draw.rectangle([(50, 50), (800, 500)], fill='white')
            
            # Layer 5: Header
            try:
                font_title = ImageFont.truetype("arialbd.ttf", 32)
                font_bold = ImageFont.truetype("arialbd.ttf", 24)
                font_regular = ImageFont.truetype("arial.ttf", 20)
                font_small = ImageFont.truetype("arial.ttf", 16)
                font_mrz = ImageFont.truetype("arial.ttf", 14)
            except:
                font_title = font_bold = font_regular = font_small = font_mrz = ImageFont.load_default()
            
            draw.text((70, 70), "UNITED KINGDOM OF", fill="#8B0000", font=font_bold)
            draw.text((70, 100), "GREAT BRITAIN AND NORTHERN IRELAND", fill="#8B0000", font=font_title)
            
            # Layer 6: Photo placeholder (gray box)
            draw.rectangle([(80, 160), (220, 335)], fill='#D3D3D3', outline='black', width=2)
            draw.text((110, 240), "PHOTO", fill='black', font=font_bold)
            
            # Layer 7: Personal details
            y_offset = 160
            
            # Surname
            surname = full_name.split()[-1] if ' ' in full_name else full_name
            given_names = full_name.replace(surname, '').strip()
            
            draw.text((250, y_offset), "Surname", fill="#666", font=font_small)
            y_offset += 25
            draw.text((250, y_offset), surname.upper(), fill="black", font=font_bold)
            
            y_offset += 45
            draw.text((250, y_offset), "Given names", fill="#666", font=font_small)
            y_offset += 25
            draw.text((250, y_offset), given_names.upper(), fill="black", font=font_bold)
            
            y_offset += 45
            draw.text((250, y_offset), "Nationality", fill="#666", font=font_small)
            y_offset += 25
            draw.text((250, y_offset), "BRITISH CITIZEN", fill="black", font=font_bold)
            
            y_offset += 50
            # Parse DOB
            dob_parts = dob_text.split()
            if len(dob_parts) == 3:
                day = dob_parts[0]
                month = dob_parts[1][:3].upper()
                year = dob_parts[2]
                dob_formatted = f"{day} {month} {year}"
            else:
                dob_formatted = dob_text
            
            draw.text((250, y_offset), f"Date of birth: {dob_formatted}", fill="black", font=font_regular)
            
            y_offset += 30
            draw.text((250, y_offset), f"Sex: {'M' if random.random() > 0.5 else 'F'}", fill="black", font=font_regular)
            
            # Passport details
            draw.text((550, 160), "Passport No.", fill="#666", font=font_small)
            draw.text((550, 185), passport_no, fill="black", font=font_bold)
            
            issue_date = datetime.now() - timedelta(days=random.randint(365, 1825))
            expiry_date = issue_date + timedelta(days=3650)
            
            draw.text((550, 230), "Date of issue", fill="#666", font=font_small)
            draw.text((550, 255), issue_date.strftime("%d %b %Y").upper(), fill="black", font=font_regular)
            
            draw.text((550, 300), "Date of expiry", fill="#666", font=font_small)
            draw.text((550, 325), expiry_date.strftime("%d %b %Y").upper(), fill="black", font=font_regular)
            
            # Layer 8: MRZ (Machine Readable Zone)
            mrz_y = 430
            draw.rectangle([(50, mrz_y), (800, mrz_y + 60)], fill='#F5F5F5')
            
            # Generate MRZ lines
            name_mrz = f"{surname.upper()}<<{given_names.upper().replace(' ', '<')}"
            name_mrz = name_mrz[:39]
            name_mrz = name_mrz + '<' * (39 - len(name_mrz))
            
            mrz1 = f"P<GBR{name_mrz}"
            
            # Parse DOB for MRZ format (YYMMDD)
            if len(dob_parts) == 3:
                yy = year[-2:]
                mm_dict = {"JAN":"01","FEB":"02","MAR":"03","APR":"04","MAY":"05","JUN":"06",
                          "JUL":"07","AUG":"08","SEP":"09","OCT":"10","NOV":"11","DEC":"12"}
                mm = mm_dict.get(month, "01")
                dd = day.zfill(2)
                dob_mrz = f"{yy}{mm}{dd}"
            else:
                dob_mrz = "000101"
            
            sex_code = 'M' if random.random() > 0.5 else 'F'
            expiry_mrz = expiry_date.strftime("%y%m%d")
            
            passport_no_clean = passport_no.replace("GB", "")
            mrz2 = f"{passport_no}{' '*(9-len(passport_no))}GBR{dob_mrz}{sex_code}{expiry_mrz}{'<'*14}00"
            
            draw.text((60, mrz_y + 10), mrz1, fill="black", font=font_mrz)
            draw.text((60, mrz_y + 30), mrz2, fill="black", font=font_mrz)
            
            # Composite all layers
            final = bg.convert('RGBA')
            final = Image.alpha_composite(final, holo)
            final = Image.alpha_composite(final, uv)
            final = final.convert('RGB')
            
            # Save image
            filename = f"uk_passport_{passport_no}.png"
            filepath = os.path.join(output_dir, filename)
            final.save(filepath, "PNG")
            
            passports.append({
                "filename": filename,
                "name": full_name,
                "passport_no": passport_no,
                "dob": dob_formatted,
                "issue_date": issue_date.strftime("%d %b %Y").upper(),
                "expiry_date": expiry_date.strftime("%d %b %Y").upper()
            })
        
        return {
            "status": "success",
            "message": f"Successfully generated {len(passports)} UK passports with multi-layer security features",
            "data": {
                "passports": passports,
                "count": len(passports),
                "output_folder": output_dir,
                "features": ["Background Pattern", "Hologram Layer", "UV Effect", "Photo Area", "MRZ Code"],
                "source": f"Individual JSON files from {docs_dir} folder",
                "processed_files": len(selected_files)
            }
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Error generating UK passports: {str(e)}",
            "traceback": traceback.format_exc()
        }

@router.post("/generate-credit-cards")
async def generate_credit_cards(request: Dict):
    """💳 Generate valid credit cards with BIN 414720 using Luhn algorithm"""
    try:
        import random
        
        # Get count from request
        count = request.get("count", 10)
        if count > 100:
            count = 100  # Limit to 100 cards
        
        def luhn_checksum(card_number):
            """Calculate Luhn checksum for credit card validation"""
            total = 0
            for i, digit in enumerate(reversed(card_number)):
                d = int(digit)
                if i % 2 == 1:
                    d *= 2
                    if d > 9:
                        d -= 9
                total += d
            check = (10 - (total % 10)) % 10
            return str(check)
        
        cards = []
        
        for i in range(count):
            # Generate card with BIN 414720
            base_number = "414720" + "".join([str(random.randint(0, 9)) for _ in range(9)])
            check_digit = luhn_checksum(base_number)
            card_number = base_number + check_digit
            
            # Generate expiry date
            month = random.randint(1, 12)
            year = random.randint(2026, 2030)
            
            # Generate CVV
            cvv = random.randint(100, 999)
            
            # Full format
            full_format = f"{card_number}|{month:02d}|{year}|{cvv}"
            
            cards.append({
                "card_number": card_number,
                "expiry": f"{month:02d}/{year}",
                "cvv": cvv,
                "full_format": full_format
            })
        
        return {
            "status": "success",
            "message": f"Successfully generated {len(cards)} valid credit cards",
            "data": {
                "cards": cards,
                "count": len(cards),
                "bin": "414720",
                "validation": "Luhn algorithm verified"
            }
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Error generating credit cards: {str(e)}",
            "traceback": traceback.format_exc()
        }

@router.post("/generate-credit-reports")
async def generate_credit_reports(request: Dict):
    """📄 Generate fake credit reports in PDF format using passport data"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import random
        import os
        import json
        import glob
        
        # Get count from request
        count = request.get("count", 10)
        if count > 100:
            count = 100  # Limit to 100 reports
        
        # Create output directory if not exists
        output_dir = "static/CreditReports"
        os.makedirs(output_dir, exist_ok=True)
        
        # Read all individual JSON files from Docs folder
        docs_dir = "static/Docs"
        json_files = glob.glob(os.path.join(docs_dir, "*.json"))
        
        # Filter out index file
        json_files = [f for f in json_files if not f.endswith("passports_index.json")]
        
        # If no passport data exists, return error
        if not json_files:
            return {
                "status": "error",
                "message": "No passport data found. Please generate documents first using the Document Generator tab."
            }
        
        # Limit count to available passport files
        count = min(count, len(json_files))
        
        # Read data from individual JSON files
        selected_files = random.sample(json_files, count) if len(json_files) > count else json_files
        
        reports = []
        
        for json_file in selected_files:
            with open(json_file, "r", encoding="utf-8") as f:
                passport_data = json.load(f)
            
            full_name = passport_data["name"]
            dob = passport_data["dob"]
            address = passport_data["address"]
            
            # Generate credit score
            credit_score = random.randint(650, 850)
            
            # Create PDF
            filename = f"credit_report_{random.randint(100000, 999999)}.pdf"
            filepath = os.path.join(output_dir, filename)
            
            c = canvas.Canvas(filepath, pagesize=letter)
            
            # Title
            c.setFont("Helvetica-Bold", 18)
            c.drawString(100, 750, "CREDIT REPORT - EXPERIAN")
            
            # Horizontal line
            c.line(100, 740, 500, 740)
            
            # Personal Information
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, 710, "Personal Information")
            
            c.setFont("Helvetica", 12)
            c.drawString(100, 685, f"Name: {full_name}")
            c.drawString(100, 665, f"Date of Birth: {dob}")
            c.drawString(100, 645, f"Address: {address}")
            
            # Credit Score Section
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, 610, "Credit Score")
            
            c.setFont("Helvetica-Bold", 16)
            score_color = "green" if credit_score >= 750 else ("orange" if credit_score >= 700 else "red")
            c.drawString(100, 585, f"Score: {credit_score}")
            
            c.setFont("Helvetica", 11)
            rating = "Excellent" if credit_score >= 750 else ("Good" if credit_score >= 700 else "Fair")
            c.drawString(200, 587, f"({rating})")
            
            # Account Information
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, 550, "Account Summary")
            
            c.setFont("Helvetica", 12)
            num_accounts = random.randint(5, 12)
            c.drawString(100, 525, f"Total Accounts: {num_accounts}")
            c.drawString(100, 505, f"Open Accounts: {random.randint(3, num_accounts)}")
            c.drawString(100, 485, f"Closed Accounts: {random.randint(0, 3)}")
            
            # Payment History
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, 450, "Payment History")
            
            c.setFont("Helvetica", 12)
            on_time_percentage = random.randint(95, 100)
            c.drawString(100, 425, f"On-time Payments: {on_time_percentage}% (last 24 months)")
            c.drawString(100, 405, f"Late Payments: {100 - on_time_percentage}%")
            c.drawString(100, 385, f"Delinquencies: {random.randint(0, 2)}")
            
            # Credit Accounts
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, 350, "Active Credit Accounts")
            
            c.setFont("Helvetica", 11)
            accounts = ["Visa Signature", "Mastercard Platinum", "American Express Gold", 
                       "Discover It", "Chase Sapphire", "Citi Double Cash"]
            y_pos = 325
            for i, account in enumerate(random.sample(accounts, min(4, len(accounts)))):
                c.drawString(110, y_pos, f"• {account} - ${random.randint(2000, 15000):,} limit")
                y_pos -= 20
            
            # Footer
            c.setFont("Helvetica", 9)
            c.drawString(100, 100, "This is a simulated credit report for testing purposes only.")
            c.drawString(100, 85, "Generated by KJC Testing Services")
            c.drawString(100, 70, f"Report Date: {random.choice(['01','15'])}/{random.randint(1,12):02d}/{random.randint(2024,2025)}")
            
            c.save()
            
            reports.append({
                "filename": filename,
                "name": full_name,
                "dob": dob,
                "address": address,
                "credit_score": credit_score,
                "rating": rating
            })
        
        return {
            "status": "success",
            "message": f"Successfully generated {len(reports)} credit reports",
            "data": {
                "reports": reports,
                "count": len(reports),
                "output_folder": output_dir,
                "source": f"Passport data from {docs_dir} folder"
            }
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Error generating credit reports: {str(e)}",
            "traceback": traceback.format_exc()
        }

@router.post("/make-docs")
async def make_docs(request: Dict):
    """📄 Generate fake passport documents for testing purposes"""
    try:
        import random
        import json
        import os
        
        # Create Docs directory if not exists
        docs_dir = "static/Docs"
        os.makedirs(docs_dir, exist_ok=True)
        
        # Sample data for generating fake passports
        first_names = ["Oliver", "Harry", "Jack", "George", "Charlie", "Jacob", "Thomas", "Oscar", "William", "James",
                      "Emily", "Olivia", "Amelia", "Isla", "Ava", "Jessica", "Poppy", "Sophie", "Lily", "Grace"]
        last_names = ["Smith", "Taylor", "Brown", "Wilson", "Johnson", "Davies", "Robinson", "Wright", "Thompson", "Evans",
                     "Walker", "White", "Roberts", "Green", "Hall", "Wood", "Jackson", "Clarke", "Patel", "Khan"]
        streets = ["High Street", "Church Road", "Main Street", "Station Road", "Park Lane", "Victoria Road", "Green Lane",
                  "Manor Road", "Queens Road", "King Street", "The Avenue", "Mill Road", "School Lane", "North Road", "South Street"]
        cities = ["London", "Manchester", "Birmingham", "Leeds", "Liverpool", "Sheffield", "Bristol", "Newcastle", "Nottingham",
                 "Leicester", "Edinburgh", "Glasgow", "Cardiff", "Belfast", "Southampton"]
        postcodes = ["SW1A 1AA", "M1 1AB", "B1 1CD", "LS1 1EF", "L1 1GH", "S1 1IJ", "BS1 1KL", "NE1 1MN", "NG1 1OP",
                    "LE1 1QR", "EH1 1ST", "G1 1UV", "CF1 1WX", "BT1 1YZ", "SO14 0AA"]
        
        # Get number of passports from request, default to 10
        num_passports = request.get("count", 10)
        num_passports = max(1, min(100, num_passports))  # Limit between 1 and 100
        passports = []
        
        for i in range(num_passports):
            # Generate random passport data
            passport_letter = random.choice(['G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S'])
            passport_number = passport_letter + ''.join([str(random.randint(0, 9)) for _ in range(8)])
            
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            full_name = f"{first_name} {last_name}"
            
            # Generate random DOB (between 1960 and 2005)
            day = random.randint(1, 28)
            months = ["January", "February", "March", "April", "May", "June", "July", "August", 
                     "September", "October", "November", "December"]
            month = random.choice(months)
            year = random.randint(1960, 2005)
            dob = f"{day} {month} {year}"
            
            # Generate random address
            house_number = random.randint(1, 999)
            street = random.choice(streets)
            city = random.choice(cities)
            postcode = random.choice(postcodes)
            address = f"{house_number} {street}, {city} {postcode}"
            
            passport_data = {
                "passport_number": passport_number,
                "name": full_name,
                "dob": dob,
                "address": address
            }
            
            passports.append(passport_data)
            
            # Save each passport to individual JSON file
            individual_file = os.path.join(docs_dir, f"{passport_number}.json")
            with open(individual_file, "w", encoding="utf-8") as f:
                json.dump(passport_data, f, indent=2, ensure_ascii=False)
        
        # Also save a master index file for easy lookup
        index_file = os.path.join(docs_dir, "passports_index.json")
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(passports, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "success",
            "message": "Fake passport documents generated successfully",
            "data": {
                "passports": passports,
                "count": len(passports),
                "saved_to": docs_dir,
                "index_file": index_file,
                "individual_files": [f"{p['passport_number']}.json" for p in passports]
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error generating documents: {str(e)}"
        }
