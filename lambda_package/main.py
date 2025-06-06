import os
import pytz
from datetime import datetime, timedelta
from notion_client import Client
from dotenv import load_dotenv
import random

# Load environment variables from .env file
load_dotenv()

# Use proper environment variable retrieval
notion = Client(auth=os.environ.get("NOTION_API_KEY"))

# Your Notion database ID - Fixed to use proper environment variable retrieval
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
# Timezone setting - change to your timezone
TIMEZONE = pytz.timezone('Asia/Kolkata')  # Change to your timezone

def get_current_day():
    """Get the current day of the week"""
    now = datetime.now(TIMEZONE)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[now.weekday()]

def get_time_block(time_str, date):
    """Convert time string to datetime object"""
    if "-" in time_str:
        # Extract start time from range (e.g., "7:30-8:00 AM" -> "7:30 AM")
        time_str = time_str.split("-")[0].strip()

    hour, minute = map(int, time_str.replace(" AM", "").replace(" PM", "").split(":"))
    if "PM" in time_str and hour != 12:
        hour += 12
    if "AM" in time_str and hour == 12:
        hour = 0

    return datetime(
        date.year, date.month, date.day, hour, minute, tzinfo=TIMEZONE
    ).isoformat()

def parse_time_range(time_range, date):
    """Parse a time range like '7:30-8:00 AM' into start and end times"""
    if "-" not in time_range:
        # If there's no range, default to 1 hour duration
        start_time = time_range
        start_hour, start_minute = map(int, start_time.replace(" AM", "").replace(" PM", "").split(":"))
        is_pm = "PM" in start_time
        is_am = "AM" in start_time

        if is_pm and start_hour != 12:
            start_hour += 12
        if is_am and start_hour == 12:
            start_hour = 0

        # Create datetime objects
        start_dt = datetime(date.year, date.month, date.day, start_hour, start_minute, tzinfo=TIMEZONE)
        end_dt = start_dt + timedelta(hours=1)
        return start_dt.isoformat(), end_dt.isoformat()

    # Split into start and end times
    parts = time_range.split("-")
    start_time = parts[0].strip()
    end_time = parts[1].strip()

    # Parse the start time
    start_hour, start_minute = map(int, start_time.replace(" AM", "").replace(" PM", "").split(":"))
    is_pm = "PM" in start_time
    is_am = "AM" in start_time

    if is_pm and start_hour != 12:
        start_hour += 12
    if is_am and start_hour == 12:
        start_hour = 0

    # Parse the end time
    end_hour, end_minute = map(int, end_time.replace(" AM", "").replace(" PM", "").split(":"))
    is_pm = "PM" in end_time
    is_am = "AM" in end_time

    if is_pm and end_hour != 12:
        end_hour += 12
    if is_am and end_hour == 12:
        end_hour = 0

    # Create datetime objects
    start_dt = datetime(date.year, date.month, date.day, start_hour, start_minute, tzinfo=TIMEZONE)
    end_dt = datetime(date.year, date.month, date.day, end_hour, end_minute, tzinfo=TIMEZONE)

    return start_dt.isoformat(), end_dt.isoformat()


def get_category_from_time(time_str):
    return None

def create_notion_event(title, time_range, details, checkbox_items, category=None, color=None):
    """Create a single event in Notion with proper structure
    
    Args:
        title (str): Title of the event
        time_range (str): Time range like "7:30-8:00 AM"
        details (str): Rich text description
        checkbox_items (list): List of tasks to complete
        category (str): Morning/Afternoon/Evening
        color (str): Color for the event (blue, red, green, yellow, orange, pink, purple, brown, gray)
                    This will be visible as a colored dot/tag in the Notion interface
    """
    today = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    
    try:
        # Create properties for the Notion page
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Date": {
                "date": {
                    "start": today
                }
            },
            "Time": {
                "rich_text": [
                    {
                        "text": {
                            "content": time_range
                        }
                    }
                ]
            },
            "Details": {
                "rich_text": [
                    {
                        "text": {
                            "content": details
                        }
                    }
                ]
            }
        }
        
        # Add category if provided
        if category:
            properties["Category"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": category
                        }
                    }
                ]
            }
        
        # Add color if provided (using a rich_text property)
        if color:
            properties["Color"] = {
               "rich_text": [
                    {
                        "text": {
                            "content": color
                        }
                    }
                ]
            }
        
        # Create the page in Notion
        page = notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties
        )
        
        # Check if page was created successfully
        if page:
            print(f"Created event: {title} successfully in Notion with color: {color}")
        else:
            print(f"Failed to create event: {title}.")
        
        # Add checkbox items if provided
        if checkbox_items and page:
            children = []
            for item in checkbox_items:
                children.append({
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": item}}],
                        "checked": False
                    }
                })
            
            if children:
                response = notion.blocks.children.append(
                    block_id=page["id"],
                    children=children
                )
                
                if response:
                    print(f"Added checklist items for {title}.")
                else:
                    print(f"Failed to add checklist items for {title}.")
        
        return page
    
    except Exception as e:
        print(f"Error creating event {title}: {e}")
        return None

def remove_tasks_without_todays_date():
    """Removes all tasks from the database that don't have today's date."""
    today = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    
    try:
        tasks = []
        has_more = True
        next_cursor = None
        
        # Get all tasks with pagination
        while has_more:
            # Query parameters
            query_params = {
                "database_id": DATABASE_ID,
                "page_size": 100  # Maximum allowed by Notion API
            }
            
            # Add start_cursor if we have one from previous pagination
            if next_cursor:
                query_params["start_cursor"] = next_cursor
                
            # Execute query
            response = notion.databases.query(**query_params)
            
            # Add results to our tasks list
            tasks.extend(response.get("results", []))
            
            # Check if there are more results
            has_more = response.get("has_more", False)
            next_cursor = response.get("next_cursor")
            
            # Print progress
            print(f"Fetched {len(response.get('results', []))} tasks from Notion database...")
        
        print(f"Total tasks retrieved: {len(tasks)}")
        
        if not tasks:
            print("No tasks found in the database.")
            return 0
        
        tasks_to_remove = []
        
        # Filter tasks manually
        for task in tasks:
            date_property = task.get("properties", {}).get("Date", {})
            date_value = date_property.get("date", {})
            
            # Check if date is empty (None) or not equal to today
            if date_value is None or date_value.get("start") != today:
                tasks_to_remove.append(task)
        
        print(f"Found {len(tasks_to_remove)} tasks without today's date ({today}).")
        
        # Archive each task that doesn't have today's date
        for task in tasks_to_remove:
            notion.pages.update(
                page_id=task["id"],
                archived=True  # This effectively deletes the page in Notion
            )
            print(f"Removed task: {task['id']}")
        
        print(f"Successfully removed {len(tasks_to_remove)} task(s) that didn't have today's date = {today}.")
        return len(tasks_to_remove)
    
    except Exception as e:
        print(f"Error removing tasks: {e}")
        return 0
    
def get_events_for_day(date):
    """Get all events for a specific day of the week
    
    Args:
        date: The date for which to get events
        
    Returns:
        A list of event dictionaries for the specified date
    """
    # Get the day of the week (0 is Monday in Python's datetime)
    day = date.weekday()
    
    # Map day number to appropriate function
    if day == 0:  # Monday
        return get_monday_events(date)
    elif day == 1:  # Tuesday
        return get_tuesday_events(date)
    elif day == 2:  # Wednesday
        return get_wednesday_events(date)
    elif day == 3:  # Thursday
        return get_thursday_events(date)
    elif day == 4:  # Friday
        return get_friday_events(date)
    elif day == 5:  # Saturday
        return get_saturday_events(date)
    elif day == 6:  # Sunday
        return get_sunday_events(date)
    else:
        # This should never happen, but just in case
        return [{
            "title": "No events scheduled",
            "time": "All day",
            "details": "This day doesn't have a specific schedule",
            "checkbox_items": ["Plan your day according to priorities"]
            # Color will be assigned randomly
        }]

def create_events_for_day(date):
    """Create events in Notion for a specific day"""
    events = get_events_for_day(date)
    created_count = 0
    
    # Remove tasks that don't have today's date
    removed_count = remove_tasks_without_todays_date()
    print(f"Removed {removed_count} tasks without today's date")

    for event in reversed(events):
        title = event["title"]
        time_range = event["time"]
        details = event["details"]
        checkbox_items = event.get("checkbox_items", [])
        
        # Get a random color
        color = get_random_color()
        
        # Parse the time range into start and end times
        start_time, end_time = parse_time_range(time_range, date)

        # Create the event in Notion
        result = create_notion_event(
            title=title, 
            time_range=time_range, 
            details=details, 
            checkbox_items=checkbox_items,
            category=get_category_from_time(time_range),
            color=color
        )
        if result:
            created_count += 1
    
    return created_count


def get_random_color():
    """Return a random color from Notion's available colors"""
    notion_colors = [
        "blue", "red", "green", "yellow", "orange", 
        "pink", "purple", "brown", "gray", "default"
    ]
    # Add weight to make some colors appear more frequently
    weighted_colors = notion_colors + ["blue", "green", "purple", "pink", "orange"]
    return random.choice(weighted_colors)

def lambda_handler(event, context):
    """AWS Lambda handler function"""
    try:
        # Get today's date
        today = datetime.now(TIMEZONE)
        
        # First remove tasks that don't have today's date, then create events
        print(f"Starting process for {get_current_day()} ({today.strftime('%Y-%m-%d')})")
        
        # Create events for today in Notion
        created_count = create_events_for_day(today)
        
        # Return success response
        return {
            'statusCode': 200,
            'body': f"Successfully processed tasks and created {created_count} events for {get_current_day()}"
        }
    except Exception as e:
        # Log any errors
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }

def get_monday_events(date):
    """Get Monday's events"""
    events = []
    
    # Morning Preparation
    events.append({
        "title": "Morning Preparation (7:30-8:00 AM)",
        "time": "7:30-8:00 AM",
        "details": "Bio break, hydration, active recall, prime the brain",
        "checkbox_items": [
            "7:30-7:40 AM: Bio break and hydration (10-minute wake-up stretching, 16oz water with lemon, review day's objectives)",
            "7:40-7:50 AM: Active recall of yesterday's concepts",
            "7:50-8:00 AM: Prime the brain (5-minute focused breathing, review schedule)"
        ]
    })
    
    # Morning Sessions
    events.append({
        "title": "Set the stage",
        "time": "8:00-8:10 AM",
        "details": "Create a concept map for today's OOPS learning",
        "checkbox_items": [
            "Create a concept map for today's OOPS learning",
            "Set specific completion criteria",
            "Prepare questions you want to answer"
        ]
    })
    
    events.append({
        "title": "CS Fundamentals Deep Focus (OOPS)",
        "time": "8:10-9:55 AM",
        "details": "Focus on Object-Oriented Programming concepts",
        "checkbox_items": [
            "First 10 min: Active recall quiz on previous OOP concepts",
            "20 min: Study new concept with focused attention",
            "10 min: Create visual representation (dual coding)",
            "20 min: Write explanations in your own words",
            "20 min: Implement small code examples (application)",
            "25 min: Create challenge problems for yourself and solve them"
        ]
    })
    
    events.append({
        "title": "Mindful break",
        "time": "9:55-10:15 AM",
        "details": "Physical movement, hydration, meditation",
        "checkbox_items": [
            "5 min: Physical movement (jumping jacks, stretches)",
            "5 min: Hydration and protein-rich snack",
            "10 min: Brief meditation focused on consolidation"
        ]
    })
    
    events.append({
        "title": "CP Practice",
        "time": "10:15-12:15 PM",
        "details": "Competitive Programming Practice",
        "checkbox_items": [
            "15 min: Review spaced repetition cards of algorithm patterns",
            "30 min: Solve problem #1 with self-explanation technique",
            "30 min: Solve problem #2 with different approach",
            "30 min: Solve problem #3 with time constraint",
            "15 min: Create summary comparing all approaches (metacognition)"
        ]
    })
    
    events.append({
        "title": "Active recovery",
        "time": "12:15-12:30 PM",
        "details": "Contralateral movements, deep breathing",
        "checkbox_items": [
            "Contralateral movements (cross-body exercises)",
            "Deep breathing (4-7-8 technique)",
            "Brain oxygenation stretches"
        ]
    })
    
    # Afternoon Sessions
    events.append({
        "title": "AIML/Web Dev Application",
        "time": "12:30-2:30 PM",
        "details": "Apply morning's concepts to project",
        "checkbox_items": [
            "10 min: Connect morning's OOP concepts to current project",
            "30 min: Design phase with visual mapping",
            "60 min: Implementation with deliberate practice",
            "20 min: Test and document with explanatory notes",
            "10 min: Identify conceptual connections (interleaving)"
        ]
    })
    
    events.append({
        "title": "Movement break",
        "time": "2:30-2:45 PM",
        "details": "Short outdoor walk, hydration",
        "checkbox_items": [
            "Short outdoor walk (nature exposure for cognitive benefits)",
            "Hydration with electrolytes",
            "Brief stretching sequence"
        ]
    })
    
    events.append({
        "title": "Lunch break + learning consolidation",
        "time": "2:45-3:30 PM",
        "details": "Protein-rich meal, learning consolidation",
        "checkbox_items": [
            "Eat protein-rich meal away from screens",
            "Listen to podcast related to morning topics",
            "Brief visualization of concepts learned"
        ]
    })
    
    events.append({
        "title": "Brainstorming with Feynman Technique",
        "time": "3:30-5:30 PM",
        "details": "Identify complex problem, break down into components",
        "checkbox_items": [
            "20 min: Identify complex problem related to morning topics",
            "40 min: Break down into explainable components",
            "50 min: Develop solution while \"teaching\" it (record audio)",
            "10 min: Create visual diagrams of solution process"
        ]
    })
    
    events.append({
        "title": "Neurocognitive reset",
        "time": "5:30-5:45 PM",
        "details": "Bilateral stimulation exercises, hydration",
        "checkbox_items": [
            "Bilateral stimulation exercises",
            "Hydration with glucose boost (fruit)",
            "Brief progressive muscle relaxation"
        ]
    })
    
    # Evening Sessions
    events.append({
        "title": "Interview Practice (DSA Focus)",
        "time": "5:45-6:45 PM",
        "details": "DSA focus with verbalized reasoning",
        "checkbox_items": [
            "10 min: Select targeted data structure and review patterns",
            "15 min: Problem #1 with verbalized reasoning",
            "15 min: Problem #2 with time constraint",
            "15 min: Create optimized solution document",
            "10 min: Create spaced repetition cards for key insights"
        ]
    })
    
    events.append({
        "title": "Active reflection",
        "time": "6:45-7:00 PM",
        "details": "Learning triangle, cross-topic connections",
        "checkbox_items": [
            "Complete learning triangle (what/so what/now what)",
            "Identify cross-topic connections",
            "Schedule specific concepts for spaced review"
        ]
    })
    
    events.append({
        "title": "Dinner + diffuse mode thinking",
        "time": "7:00-8:30 PM",
        "details": "Nutritious meal, gentle activity",
        "checkbox_items": [
            "Nutritious meal with omega-3 fatty acids",
            "Gentle physical activity",
            "Allow mind to wander for incubation effect"
        ]
    })
    
    events.append({
        "title": "CS Fundamentals Revision with Retrieval Practice",
        "time": "8:30-9:15 PM",
        "details": "Write everything you remember about today's topics",
        "checkbox_items": [
            "10 min: Write everything you remember about today's OOP topics",
            "15 min: Check against notes and fill gaps",
            "15 min: Create analogies and metaphors for difficult concepts",
            "5 min: Schedule next review using optimal spacing algorithm"
        ]
    })
    
    events.append({
        "title": "Finance Studies with Application",
        "time": "9:15-10:00 PM",
        "details": "Learn one new financial concept",
        "checkbox_items": [
            "Learn one new financial concept with real-world example",
            "Create decision tree for practical application",
            "Connect to personal financial goals",
            "Schedule implementation steps"
        ]
    })
    
    # Evening Wind-Down
    events.append({
        "title": "Evening Wind-Down",
        "time": "10:00-11:30 PM",
        "details": "Brain dump, next day preparation, relaxation, sleep",
        "checkbox_items": [
            "10:00-10:15 PM: Brain dump and reset (write down everything learned today, identify 3 key insights, brief mindfulness practice)",
            "10:15-10:45 PM: Next day preparation (review topics, organize workspace, set 3 specific goals)",
            "10:45-11:15 PM: Screen-free relaxation (read physical book, visualization exercise, gratitude journaling)",
            "11:15-11:30 PM: Sleep preparation ritual (no screens, set room temperature, sleep intention setting)",
            "11:30 PM: Sleep (6.5 hours)"
        ]
    })
    
    return events

def get_tuesday_events(date):
    """Get Tuesday's events"""
    events = []
    
    # Morning Preparation
    events.append({
        "title": "Morning Preparation (7:30-8:00 AM)",
        "time": "7:30-8:00 AM",
        "details": "Bio break, hydration, active recall, prime the brain",
        "checkbox_items": [
            "7:30-7:40 AM: Bio break and hydration (10-minute wake-up stretching, 16oz water with lemon, review day's objectives)",
            "7:40-7:50 AM: Active recall of yesterday's concepts",
            "7:50-8:00 AM: Prime the brain (5-minute focused breathing, review schedule)"
        ]
    })
    
    # Morning Sessions
    events.append({
        "title": "Set the stage",
        "time": "8:00-8:10 AM",
        "details": "Brief review of learning objectives",
        "checkbox_items": [
            "Brief review of learning objectives",
            "Connect today's OS topics to yesterday's OOP concepts",
            "Prepare specific questions to answer"
        ]
    })
    
    events.append({
        "title": "CS Fundamentals (OS Concepts)",
        "time": "8:10-9:55 AM",
        "details": "Learn OS concepts, create visual models",
        "checkbox_items": [
            "15 min: Active recall quiz on Monday's OOP concepts",
            "20 min: Learn new OS concept using Cornell note-taking",
            "15 min: Create visual models of processes/scheduling",
            "25 min: Self-explanation of concepts (record audio)",
            "30 min: Create mini-problems demonstrating OS concepts"
        ]
    })
    
    events.append({
        "title": "Mindful break",
        "time": "9:55-10:15 AM",
        "details": "Physical movement, hydration, visualization",
        "checkbox_items": [
            "5 min: Physical movement (different from Monday)",
            "5 min: Hydration and different healthy snack",
            "10 min: Brief visualization of concepts mastered"
        ]
    })
    
    events.append({
        "title": "CP Practice (Algorithm Implementation)",
        "time": "10:15-12:15 PM",
        "details": "Review, learn new algorithm, implement variations",
        "checkbox_items": [
            "10 min: Review spaced repetition cards from Monday",
            "25 min: Learn new algorithm with dual coding",
            "30 min: Implement variation #1 with verbalization",
            "30 min: Implement variation #2 with optimization focus",
            "25 min: Compare approaches and extract patterns"
        ]
    })
    
    events.append({
        "title": "Active recovery",
        "time": "12:15-12:30 PM",
        "details": "Different movement pattern, box breathing",
        "checkbox_items": [
            "Different movement pattern from Monday",
            "Box breathing technique",
            "Quick self-massage for mental refreshment"
        ]
    })
    
    # Afternoon Sessions
    events.append({
        "title": "AIML/Web Dev Continuation",
        "time": "12:30-2:30 PM",
        "details": "Review Monday's progress, design next phase",
        "checkbox_items": [
            "15 min: Review Monday's progress with critical analysis",
            "30 min: Design next implementation phase",
            "60 min: Implementation with deliberate practice",
            "15 min: Document with teaching focus (explain to others)",
            "10 min: Create connections between OS concepts and project"
        ]
    })
    
    events.append({
        "title": "Movement break",
        "time": "2:30-2:45 PM",
        "details": "Different movement pattern, hydration",
        "checkbox_items": [
            "Different movement pattern from Monday",
            "Hydration with different nutrient profile",
            "Brief stretching sequence"
        ]
    })
    
    events.append({
        "title": "Lunch break + interleaved review",
        "time": "2:45-3:30 PM",
        "details": "Healthy fats meal, brief review",
        "checkbox_items": [
            "Eat different nutrient profile meal (healthy fats)",
            "Brief review of morning's concepts using different modality",
            "Practice 2-3 spaced repetition flashcards from Monday"
        ]
    })
    
    events.append({
        "title": "System Design with Elaborative Interrogation",
        "time": "3:30-5:30 PM",
        "details": "Design challenge incorporating OS concepts",
        "checkbox_items": [
            "15 min: Select design challenge incorporating OS concepts",
            "30 min: Create design asking \"why\" questions throughout",
            "30 min: Create architectural diagrams with annotations",
            "45 min: Document design decisions with justifications",
            "30 min: Identify potential optimizations"
        ]
    })
    
    events.append({
        "title": "Neurocognitive reset",
        "time": "5:30-5:45 PM",
        "details": "Different bilateral stimulation exercise",
        "checkbox_items": [
            "Different bilateral stimulation exercise",
            "Hydration with different nutrient profile",
            "Brief autogenic training"
        ]
    })
    
    # Evening Sessions
    events.append({
        "title": "Interview Practice (Aptitude Focus)",
        "time": "5:45-6:45 PM",
        "details": "Review frameworks, practice sets",
        "checkbox_items": [
            "10 min: Review aptitude question frameworks",
            "15 min: Practice set #1 with verbalization",
            "15 min: Practice set #2 with time constraints",
            "15 min: Create optimized approach document",
            "5 min: Schedule spaced review of challenging questions"
        ]
    })
    
    events.append({
        "title": "Active reflection with concept mapping",
        "time": "6:45-7:00 PM",
        "details": "Create mind map connecting today's learning",
        "checkbox_items": [
            "Create mind map connecting today's learning",
            "Identify cross-domain applications",
            "Schedule specific concepts for spaced review"
        ]
    })
    
    events.append({
        "title": "Dinner + diffuse mode thinking",
        "time": "7:00-8:30 PM",
        "details": "Different nutritional profile meal",
        "checkbox_items": [
            "Different nutritional profile meal",
            "Different gentle physical activity",
            "Brief creative thinking exercise"
        ]
    })
    
    events.append({
        "title": "Revision with Connection Building",
        "time": "8:30-9:15 PM",
        "details": "Active recall, connect concepts",
        "checkbox_items": [
            "10 min: Active recall of Tuesday concepts",
            "15 min: Connect OS concepts with Monday's OOP learning",
            "10 min: Create integrated examples of both domains",
            "10 min: Schedule spaced review using optimal algorithm"
        ]
    })
    
    events.append({
        "title": "Finance Studies with Analysis",
        "time": "9:15-10:00 PM",
        "details": "Study investment risk concepts",
        "checkbox_items": [
            "Study investment risk concepts with concrete examples",
            "Apply mathematical models to sample scenarios",
            "Create decision matrix for personal application",
            "Schedule implementation steps"
        ]
    })
    
    # Evening Wind-Down
    events.append({
        "title": "Evening Wind-Down",
        "time": "10:00-11:30 PM",
        "details": "Brain dump, next day preparation, relaxation, sleep",
        "checkbox_items": [
            "10:00-10:15 PM: Brain dump and reset (write down everything learned today, identify 3 key insights, brief mindfulness practice)",
            "10:15-10:45 PM: Next day preparation (review topics, organize workspace, set 3 specific goals)",
            "10:45-11:15 PM: Screen-free relaxation (read physical book, visualization exercise, gratitude journaling)",
            "11:15-11:30 PM: Sleep preparation ritual (no screens, set room temperature, sleep intention setting)",
            "11:30 PM: Sleep (6.5 hours)"
        ]
    })
    
    return events

def get_wednesday_events(date):
    """Get Wednesday's events"""
    events = []
    
    # Morning Preparation
    events.append({
        "title": "Morning Preparation (7:30-8:00 AM)",
        "time": "7:30-8:00 AM",
        "details": "Bio break, hydration, active recall, prime the brain",
        "checkbox_items": [
            "7:30-7:40 AM: Bio break and hydration (10-minute wake-up stretching, 16oz water with lemon, review day's objectives)",
            "7:40-7:50 AM: Active recall of yesterday's concepts",
            "7:50-8:00 AM: Prime the brain (5-minute focused breathing, review schedule)"
        ]
    })
    
    # Morning Sessions
    events.append({
        "title": "Set the stage",
        "time": "8:00-8:10 AM",
        "details": "Brief visualization of successful learning",
        "checkbox_items": [
            "Brief visualization of successful learning",
            "Connect today's DBMS topics to previous days' concepts",
            "Prepare specific questions to answer"
        ]
    })
    
    events.append({
        "title": "CS Fundamentals (DBMS Focus)",
        "time": "8:10-9:55 AM",
        "details": "DBMS normalization, schema diagrams, query optimization",
        "checkbox_items": [
            "15 min: Interleaved review of OOP and OS concepts",
            "20 min: Learn DBMS normalization using concrete examples",
            "20 min: Create visual schema diagrams (dual coding)",
            "30 min: Practice query optimization with think-aloud protocol",
            "20 min: Connect database concepts to system architecture"
        ]
    })
    
    events.append({
        "title": "Mindful break",
        "time": "9:55-10:15 AM",
        "details": "Different physical movement pattern, hydration",
        "checkbox_items": [
            "5 min: Different physical movement pattern",
            "5 min: Hydration with different nutrient profile",
            "10 min: Brief mindfulness practice"
        ]
    })
    
    events.append({
        "title": "CP Contest Preparation with Deliberate Practice",
        "time": "10:15-12:15 PM",
        "details": "Review algorithm templates, practice time management",
        "checkbox_items": [
            "15 min: Review algorithm templates with critical analysis",
            "30 min: Practice time management with mini-challenges",
            "45 min: Solve past contest problems with constraints",
            "30 min: Analyze solution patterns and create heuristics",
            "15 min: Mental rehearsal of contest strategies"
        ]
    })
    
    events.append({
        "title": "Active recovery",
        "time": "12:15-12:30 PM",
        "details": "Different movement pattern, breathing",
        "checkbox_items": [
            "Different movement pattern from Tuesday",
            "4-7-8 breathing technique",
            "Brief self-massage for mental refreshment"
        ]
    })
    
    # Afternoon Sessions
    events.append({
        "title": "AIML/Web Dev Integration",
        "time": "12:30-2:30 PM",
        "details": "Review progress, align with DBMS concepts",
        "checkbox_items": [
            "15 min: Review progress and align with DBMS concepts",
            "30 min: Design data persistence layer",
            "60 min: Implementation with deliberate practice",
            "30 min: Create comprehensive test suite",
            "15 min: Document with teaching focus"
        ]
    })
    
    events.append({
        "title": "Movement break",
        "time": "2:30-2:45 PM",
        "details": "Different movement pattern, hydration",
        "checkbox_items": [
            "Different movement pattern",
            "Hydration with different nutrient profile",
            "Brief energizing stretches"
        ]
    })
    
    events.append({
        "title": "Lunch break + interleaved learning",
        "time": "2:45-3:30 PM",
        "details": "Different nutritional profile meal, brief review",
        "checkbox_items": [
            "Different nutritional profile meal",
            "Brief review using different modality",
            "Practice spaced repetition flashcards from previous days"
        ]
    })
    
    events.append({
        "title": "Problem Solving with Desirable Difficulty",
        "time": "3:30-5:30 PM",
        "details": "Select challenging problem requiring DBMS concepts",
        "checkbox_items": [
            "15 min: Select challenging problem requiring DBMS concepts",
            "45 min: Solve with intentional constraints",
            "30 min: Optimize solution with performance focus",
            "30 min: Document approach with detailed explanations",
            "30 min: Create teaching materials from solution"
        ]
    })
    
    events.append({
        "title": "Pre-contest preparation",
        "time": "5:30-5:45 PM",
        "details": "Mental rehearsal of contest strategies",
        "checkbox_items": [
            "Mental rehearsal of contest strategies",
            "Hydration and energy-sustaining snack",
            "Brief progressive relaxation"
        ]
    })
    
    # Evening Sessions
    events.append({
        "title": "Interview Practice (DSA Different Topic)",
        "time": "5:45-6:45 PM",
        "details": "Select different data structure from Monday",
        "checkbox_items": [
            "10 min: Select different data structure from Monday",
            "15 min: Problem #1 with verbalized reasoning",
            "15 min: Problem #2 with time constraint",
            "15 min: Create optimized solution document",
            "5 min: Schedule spaced review of key insights"
        ]
    })
    
    events.append({
        "title": "Final Contest Preparation",
        "time": "6:45-7:00 PM",
        "details": "Review contest strategies with visualization",
        "checkbox_items": [
            "Review contest strategies with visualization",
            "Set specific, measurable goals",
            "Mental rehearsal of problem-solving approach"
        ]
    })
    
    events.append({
        "title": "Dinner + Contest Prep",
        "time": "7:00-8:00 PM",
        "details": "Balanced meal optimized for mental performance",
        "checkbox_items": [
            "Balanced meal optimized for mental performance",
            "Brief relaxation techniques",
            "Final mental preparation with visualization"
        ]
    })
    
    events.append({
        "title": "WEEKLY CONTEST with Metacognition",
        "time": "8:00-10:00 PM",
        "details": "Apply time management strategies with awareness",
        "checkbox_items": [
            "Apply time management strategies with awareness",
            "Document thinking process while solving",
            "Apply pattern recognition techniques",
            "Regular breathing and stress management during contest"
        ]
    })
    
    # Evening Wind-Down
    events.append({
        "title": "Evening Wind-Down",
        "time": "10:00-11:30 PM",
        "details": "Brain dump, next day preparation, relaxation, sleep",
        "checkbox_items": [
            "10:00-10:15 PM: Brain dump and reset (write down everything learned today, identify 3 key insights, brief mindfulness practice)",
            "10:15-10:45 PM: Next day preparation (review topics, organize workspace, set 3 specific goals)",
            "10:45-11:15 PM: Screen-free relaxation (read physical book, visualization exercise, gratitude journaling)",
            "11:15-11:30 PM: Sleep preparation ritual (no screens, set room temperature, sleep intention setting)",
            "11:30 PM: Sleep (6.5 hours)"
        ]
    })
    
    return events

def get_thursday_events(date):
    """Get Thursday's events - Analyze & Optimize"""
    events = []

    # Morning Preparation
    events.append({
        "title": "Morning Preparation",
        "time": "7:30-8:00 AM",
        "details": "Bio break, hydration, active recall, prime the brain",
        "checkbox_items": [
            "7:30-7:40 AM: Bio break and hydration (10-minute wake-up stretching, 16oz water with lemon, review day's objectives)",
            "7:40-7:50 AM: Active recall of yesterday's concepts",
            "7:50-8:00 AM: Prime the brain (5-minute focused breathing, review schedule)"
        ]
    })

    # Morning Sessions
    events.append({
        "title": "Set the stage",
        "time": "8:00-8:10 AM",
        "details": "Brief reflection and set learning objectives",
        "checkbox_items": [
            "Brief reflection on contest performance",
            "Connect today's Networking topics to previous concepts",
            "Set specific learning objectives"
        ]
    })

    events.append({
        "title": "CS Fundamentals (Computer Networks)",
        "time": "8:10-9:55 AM",
        "details": "Deep dive into networking concepts",
        "checkbox_items": [
            "15 min: Interleaved review of DBMS concepts",
            "25 min: Learn networking protocols with concrete examples",
            "20 min: Create visual network flow diagrams",
            "25 min: Solve networking problems with think-aloud protocol",
            "20 min: Connect networking concepts to distributed systems"
        ]
    })

    events.append({
        "title": "Mindful break",
        "time": "9:55-10:15 AM",
        "details": "Physical movement, hydration, visualization",
        "checkbox_items": [
            "5 min: Different physical movement pattern",
            "5 min: Hydration with nutrient-rich snack",
            "10 min: Brief visualization of mastery"
        ]
    })

    events.append({
        "title": "CP Pattern Recognition with Elaborative Interrogation",
        "time": "10:15-12:15 PM",
        "details": "Analysis and pattern recognition",
        "checkbox_items": [
            "30 min: Analyze yesterday's contest problems deeply",
            "30 min: Identify recurring patterns with \"why\" questions",
            "45 min: Create optimized template solutions",
            "30 min: Practice applying templates to new problems"
        ]
    })

    events.append({
        "title": "Active recovery",
        "time": "12:15-12:30 PM",
        "details": "Movement and recovery",
        "checkbox_items": [
            "Different movement pattern",
            "Alternate breathing technique",
            "Quick sensory reset exercise"
        ]
    })

    # Afternoon Sessions
    events.append({
        "title": "AIML/Web Dev Networking Focus",
        "time": "12:30-2:30 PM",
        "details": "Implementation with networking concepts",
        "checkbox_items": [
            "15 min: Review progress and align with networking concepts",
            "30 min: Design secure communication layer",
            "60 min: Implementation with deliberate practice",
            "30 min: Create comprehensive test suite",
            "15 min: Document with security considerations"
        ]
    })

    events.append({
        "title": "Movement break",
        "time": "2:30-2:45 PM",
        "details": "Physical movement and hydration",
        "checkbox_items": [
            "Different pattern of movement",
            "Hydration with different nutrient profile",
            "Brief energizing stretches"
        ]
    })

    events.append({
        "title": "Lunch break + active learning",
        "time": "2:45-3:30 PM",
        "details": "Nutrition and active learning",
        "checkbox_items": [
            "Different nutritional profile meal",
            "Brief teaching of morning concepts (record audio)",
            "Practice spaced repetition from earlier in week"
        ]
    })

    events.append({
        "title": "System Improvement with Dual Coding",
        "time": "3:30-5:30 PM",
        "details": "Optimization using networking concepts",
        "checkbox_items": [
            "15 min: Select system to optimize using networking concepts",
            "30 min: Create visual optimization diagrams",
            "60 min: Implement optimizations with verbalization",
            "30 min: Develop performance metrics and testing",
            "15 min: Document optimization process"
        ]
    })

    events.append({
        "title": "Neurocognitive reset",
        "time": "5:30-5:45 PM",
        "details": "Recovery and hydration",
        "checkbox_items": [
            "Novel bilateral stimulation exercise",
            "Hydration with cognitive-supporting nutrients",
            "Brief progressive relaxation"
        ]
    })

    # Evening Sessions
    events.append({
        "title": "Interview Practice (HR Focus)",
        "time": "5:45-6:45 PM",
        "details": "Prepare for HR interviews",
        "checkbox_items": [
            "15 min: Prepare stories demonstrating technical skills",
            "15 min: Practice delivery with recording",
            "15 min: Self-critique and improvement",
            "15 min: Create structured response templates"
        ]
    })

    events.append({
        "title": "Active reflection with retrieval practice",
        "time": "6:45-7:00 PM",
        "details": "Reflection and planning",
        "checkbox_items": [
            "Write everything remembered from today without notes",
            "Identify knowledge gaps and create review plan",
            "Schedule spaced repetition for weak areas"
        ]
    })

    events.append({
        "title": "Dinner + diffuse mode processing",
        "time": "7:00-8:30 PM",
        "details": "Nutrition and relaxation",
        "checkbox_items": [
            "Brain-supporting nutritional profile",
            "Gentle physical activity",
            "Allow mind to wander for insight generation"
        ]
    })

    events.append({
        "title": "Contest Upsolving with Deliberate Practice",
        "time": "8:30-9:15 PM",
        "details": "Problem solving and documentation",
        "checkbox_items": [
            "Select 1-2 unsolved problems from contest",
            "Apply structured problem-solving approach",
            "Document solution with detailed explanations",
            "Create spaced repetition cards for key insights"
        ]
    })

    events.append({
        "title": "Finance Studies with Application",
        "time": "9:15-10:00 PM",
        "details": "Study portfolio theory with applications",
        "checkbox_items": [
            "Study portfolio theory with concrete examples",
            "Create sample portfolio with actual calculations",
            "Document risk management strategies",
            "Schedule implementation steps"
        ]
    })

    return events


def get_friday_events(date):
    """Get Friday's events - Review & Apply"""
    events = []

    # Morning Preparation
    events.append({
        "title": "Morning Preparation",
        "time": "7:30-8:00 AM",
        "details": "Bio break, hydration, active recall, prime the brain",
        "checkbox_items": [
            "7:30-7:40 AM: Bio break and hydration (10-minute wake-up stretching, 16oz water with lemon, review day's objectives)",
            "7:40-7:50 AM: Active recall of yesterday's concepts",
            "7:50-8:00 AM: Prime the brain (5-minute focused breathing, review schedule)"
        ]
    })

    # Morning Sessions
    events.append({
        "title": "Set the stage",
        "time": "8:00-8:10 AM",
        "details": "Weekly progress visualization and goal setting",
        "checkbox_items": [
            "Weekly progress visualization",
            "Connect system design to all week's concepts",
            "Set ambitious but specific learning goals"
        ]
    })

    events.append({
        "title": "CS Fundamentals (System Design)",
        "time": "8:10-9:55 AM",
        "details": "Study system design principles and architecture",
        "checkbox_items": [
            "15 min: Interleaved review of week's concepts",
            "25 min: Study system design principles with examples",
            "30 min: Create comprehensive architecture diagrams",
            "35 min: Practice scalability calculations and estimations",
            "15 min: Connect all week's topics into cohesive design"
        ]
    })

    events.append({
        "title": "Mindful break",
        "time": "9:55-10:15 AM",
        "details": "Movement, hydration, visualization",
        "checkbox_items": [
            "5 min: Novel physical movement",
            "5 min: Hydration and brain-supporting snack",
            "10 min: Brief visualization of integrated knowledge"
        ]
    })

    events.append({
        "title": "CP Advanced Techniques with Deliberate Constraints",
        "time": "10:15-12:15 PM",
        "details": "Focus on advanced techniques and implementation",
        "checkbox_items": [
            "15 min: Select advanced technique for mastery focus",
            "30 min: Study mathematical foundations",
            "45 min: Implement technique with progressive challenges",
            "30 min: Create teaching document for future reference",
            "15 min: Design practice plan for maintenance"
        ]
    })

    events.append({
        "title": "Active recovery",
        "time": "12:15-12:30 PM",
        "details": "Full-body movement and relaxation",
        "checkbox_items": [
            "Full-body movement sequence",
            "Deep breathing technique",
            "Brief progressive relaxation"
        ]
    })

    # Afternoon Sessions
    events.append({
        "title": "AIML/Web Dev Integration Project",
        "time": "12:30-2:30 PM",
        "details": "Design and implementation of integrated components",
        "checkbox_items": [
            "15 min: Create comprehensive plan integrating week's concepts",
            "30 min: Design architecture incorporating all principles",
            "60 min: Implementation of key components",
            "30 min: Testing and documentation",
            "15 min: Plan next week's extensions"
        ]
    })

    events.append({
        "title": "Movement break",
        "time": "2:30-2:45 PM",
        "details": "Outdoor exposure and hydration",
        "checkbox_items": [
            "Short outdoor exposure (nature boost)",
            "Hydration with different nutrient profile",
            "Brief energizing stretches"
        ]
    })

    events.append({
        "title": "Lunch break + conceptual integration",
        "time": "2:45-3:30 PM",
        "details": "Brain-supporting meal and concept mapping",
        "checkbox_items": [
            "Brain-supporting meal",
            "Create concept map of week's learning",
            "Brief spaced repetition practice"
        ]
    })

    events.append({
        "title": "Weekly Integration with Feynman Technique",
        "time": "3:30-5:30 PM",
        "details": "Comprehensive explanation and teaching",
        "checkbox_items": [
            "30 min: Select complex topic combining week's learning",
            "60 min: Create comprehensive explanation (as if teaching)",
            "30 min: Develop visual aids and diagrams",
            "30 min: Create practical application examples"
        ]
    })

    events.append({
        "title": "Cognitive reset",
        "time": "5:30-5:45 PM",
        "details": "Movement and mindfulness",
        "checkbox_items": [
            "Novel movement pattern",
            "Hydration with different nutrient profile",
            "Brief mindfulness practice"
        ]
    })

    # Evening Sessions
    events.append({
        "title": "Mock Interview (Comprehensive)",
        "time": "5:45-6:45 PM",
        "details": "Complete mock interview with self-assessment",
        "checkbox_items": [
            "10 min: Mental preparation",
            "30 min: Complete full mock interview",
            "15 min: Self-assessment and critique",
            "10 min: Create focused improvement plan"
        ]
    })

    events.append({
        "title": "Week review with metacognition",
        "time": "6:45-7:00 PM",
        "details": "Review objectives and plan for weekend",
        "checkbox_items": [
            "Review learning objectives achieved",
            "Identify knowledge connections formed",
            "Create focused plan for weekend consolidation"
        ]
    })

    events.append({
        "title": "Dinner + celebration",
        "time": "7:00-8:30 PM",
        "details": "Nutritious meal and reflection",
        "checkbox_items": [
            "Nutritious meal with enjoyment focus",
            "Brief reflection on week's accomplishments",
            "Mental preparation for weekend learning"
        ]
    })

    events.append({
        "title": "Weekly Summary with Spaced Repetition Planning",
        "time": "8:30-9:15 PM",
        "details": "Create summary and review schedule",
        "checkbox_items": [
            "Create comprehensive summary document",
            "Design optimal review schedule for next week",
            "Identify most valuable concepts for maintenance",
            "Schedule specific review times"
        ]
    })

    events.append({
        "title": "Finance Studies with Integration",
        "time": "9:15-10:00 PM",
        "details": "Review financial concepts and plan application",
        "checkbox_items": [
            "Review all financial concepts from week",
            "Create practical application plan",
            "Connect to personal financial goals",
            "Schedule implementation steps"
        ]
    })

    return events


def get_saturday_events(date):
    """Get Saturday's events - Challenge & Compete"""
    events = []

    # Morning Preparation
    events.append({
        "title": "Morning Preparation",
        "time": "7:30-8:00 AM",
        "details": "Bio break, hydration, active recall, prime the brain",
        "checkbox_items": [
            "7:30-7:40 AM: Bio break and hydration (10-minute wake-up stretching, 16oz water with lemon, review day's objectives)",
            "7:40-7:50 AM: Active recall of yesterday's concepts",
            "7:50-8:00 AM: Prime the brain (5-minute focused breathing, review schedule)"
        ]
    })

    # Morning Sessions
    events.append({
        "title": "CS Fundamentals Comprehensive Review",
        "time": "8:00-10:00 AM",
        "details": "Active recall and concept mapping",
        "checkbox_items": [
            "20 min: Active recall of all week's concepts",
            "40 min: Create interconnected concept map",
            "30 min: Identify and address knowledge gaps",
            "30 min: Practice integrated problem solving"
        ]
    })

    events.append({
        "title": "Mindful break",
        "time": "10:00-10:15 AM",
        "details": "Movement, hydration, visualization",
        "checkbox_items": [
            "5 min: Novel physical movement",
            "5 min: Hydration and brain-supporting snack",
            "10 min: Brief visualization of successful learning"
        ]
    })

    events.append({
        "title": "CP Challenge Practice with Desirable Difficulty",
        "time": "10:15-12:15 PM",
        "details": "Challenging problem solving with time constraints",
        "checkbox_items": [
            "15 min: Select challenging multi-concept problems",
            "45 min: Solve with time constraints",
            "30 min: Analyze and optimize solutions",
            "30 min: Document problem-solving heuristics",
            "15 min: Create practice plan for maintaining skills"
        ]
    })

    events.append({
        "title": "Active recovery",
        "time": "12:15-12:30 PM",
        "details": "Movement and mindfulness",
        "checkbox_items": [
            "Novel movement pattern",
            "Breathing technique for focus",
            "Brief mindfulness practice"
        ]
    })

    # Afternoon Sessions
    events.append({
        "title": "AIML/Web Dev Project with Deliberate Practice",
        "time": "12:30-2:30 PM",
        "details": "Advanced feature implementation",
        "checkbox_items": [
            "15 min: Review project status and objectives",
            "30 min: Design advanced feature implementation",
            "60 min: Implementation with intentional constraints",
            "30 min: Testing and documentation",
            "15 min: Plan next week's development"
        ]
    })

    events.append({
        "title": "Movement break",
        "time": "2:30-2:45 PM",
        "details": "Movement and hydration",
        "checkbox_items": [
            "Different movement pattern",
            "Hydration with cognitive-supporting nutrients",
            "Brief energizing stretches"
        ]
    })

    events.append({
        "title": "Lunch break + learning consolidation",
        "time": "2:45-3:30 PM",
        "details": "Brain-supporting meal and review",
        "checkbox_items": [
            "Brain-supporting nutritional profile",
            "Brief review of morning's progress",
            "Mental preparation for afternoon session"
        ]
    })

    events.append({
        "title": "Deep Brainstorming with SCAMPER Technique",
        "time": "3:30-5:30 PM",
        "details": "Creative problem solving and implementation planning",
        "checkbox_items": [
            "15 min: Select challenging problem incorporating week's concepts",
            "45 min: Apply SCAMPER methodology for creative solutions",
            "45 min: Develop most promising ideas",
            "30 min: Create implementation roadmap",
            "15 min: Document process and insights"
        ]
    })

    events.append({
        "title": "Contest preparation",
        "time": "5:30-5:45 PM",
        "details": "Mental preparation and hydration",
        "checkbox_items": [
            "Mental rehearsal of contest strategies",
            "Hydration and brain-supporting snack",
            "Brief relaxation technique"
        ]
    })

    # Evening Sessions
    events.append({
        "title": "System Design Interview Practice",
        "time": "5:45-6:45 PM",
        "details": "Complex design challenge with documentation",
        "checkbox_items": [
            "10 min: Select complex design challenge",
            "20 min: Create comprehensive design with verbalization",
            "15 min: Self-critique and improvement",
            "15 min: Document design patterns and principles"
        ]
    })

    events.append({
        "title": "Contest Preparation (Biweekly)",
        "time": "6:45-7:00 PM",
        "details": "Strategy review and goal setting",
        "checkbox_items": [
            "Review contest strategies",
            "Set specific, challenging goals",
            "Final mental preparation with visualization"
        ]
    })

    events.append({
        "title": "Dinner + Contest Prep",
        "time": "7:00-8:00 PM",
        "details": "Balanced meal and mental preparation",
        "checkbox_items": [
            "Balanced meal for optimal brain function",
            "Brief relaxation techniques",
            "Final mental preparation"
        ]
    })

    events.append({
        "title": "BIWEEKLY CONTEST with Metacognition",
        "time": "8:00-10:00 PM",
        "details": "Strategic problem solving and documentation",
        "checkbox_items": [
            "Apply strategic problem selection",
            "Document thinking process during solving",
            "Regular cognitive check-ins during contest",
            "Apply pattern recognition techniques"
        ]
    })

    return events


def get_sunday_events(date):
    """Get Sunday's events - Recover & Plan"""
    events = []

    # Morning Preparation
    events.append({
        "title": "Morning Preparation",
        "time": "7:30-8:00 AM",
        "details": "Bio break, hydration, active recall, prime the brain",
        "checkbox_items": [
            "7:30-7:40 AM: Bio break and hydration (10-minute wake-up stretching, 16oz water with lemon, review day's objectives)",
            "7:40-7:50 AM: Active recall of yesterday's concepts",
            "7:50-8:00 AM: Prime the brain (5-minute focused breathing, review schedule)"
        ]
    })

    # Morning Sessions
    events.append({
        "title": "WEEKLY CONTEST with Strategic Approach",
        "time": "8:00-10:00 AM",
        "details": "Strategic contest participation",
        "checkbox_items": [
            "Apply all week's learning strategically",
            "Use time management techniques",
            "Apply pattern recognition for problem selection",
            "Document approaches for later review"
        ]
    })

    events.append({
        "title": "Mindful break",
        "time": "10:00-10:15 AM",
        "details": "Recovery movement and hydration",
        "checkbox_items": [
            "Recovery movement",
            "Hydration and nutrient replenishment",
            "Brief mindfulness practice"
        ]
    })

    events.append({
        "title": "Contest Upsolving with Deliberate Practice",
        "time": "10:15-12:15 PM",
        "details": "Systematic analysis and implementation",
        "checkbox_items": [
            "Analyze all contest problems systematically",
            "Study efficient solutions with deep understanding",
            "Implement solutions with verbalization",
            "Create template solutions for future reference",
            "Schedule spaced review of techniques"
        ]
    })

    events.append({
        "title": "Active recovery",
        "time": "12:15-12:30 PM",
        "details": "Full-body movement and relaxation",
        "checkbox_items": [
            "Full-body movement sequence",
            "Deep breathing technique",
            "Brief progressive relaxation"
        ]
    })

    # Afternoon Sessions
    events.append({
        "title": "Weekly Planning with OKR Approach",
        "time": "12:30-2:30 PM",
        "details": "Review accomplishments and set objectives",
        "checkbox_items": [
            "Review previous week's accomplishments",
            "Set specific objectives for coming week",
            "Create detailed key results for each objective",
            "Align with monthly learning roadmap",
            "Prepare resources for Monday's topics"
        ]
    })

    events.append({
        "title": "Movement break",
        "time": "2:30-2:45 PM",
        "details": "Nature exposure and hydration",
        "checkbox_items": [
            "Nature exposure if possible",
            "Hydration with recovery nutrients",
            "Brief stretching sequence"
        ]
    })

    events.append({
        "title": "Lunch + extended break",
        "time": "2:45-3:30 PM",
        "details": "Nutritious meal and mental disconnection",
        "checkbox_items": [
            "Nutritious recovery meal",
            "Complete mental disconnection",
            "Light physical activity"
        ]
    })

    events.append({
        "title": "Weekly Review & Planning with Interleaving",
        "time": "3:30-5:30 PM",
        "details": "Comprehensive review and planning",
        "checkbox_items": [
            "Create comprehensive review of all topics",
            "Identify connections between domains",
            "Create spaced repetition schedule for coming week",
            "Design interleaved practice sessions",
            "Prepare study materials for Monday"
        ]
    })

    events.append({
        "title": "Mindful reset",
        "time": "5:30-5:45 PM",
        "details": "Movement and mindfulness",
        "checkbox_items": [
            "Novel movement pattern",
            "Hydration with different nutrient profile",
            "Brief mindfulness practice"
        ]
    })

    # Evening Sessions
    events.append({
        "title": "Next Week Planning with Implementation Intentions",
        "time": "5:45-6:45 PM",
        "details": "Specific planning with accountability",
        "checkbox_items": [
            "Create specific if-then plans for learning objectives",
            "Design optimal schedule incorporating spaced repetition",
            "Prepare environment and resources",
            "Create accountability measures"
        ]
    })

    events.append({
        "title": "Week closure with gratitude practice",
        "time": "6:45-7:00 PM",
        "details": "Document accomplishments and set intentions",
        "checkbox_items": [
            "Document specific learning accomplishments",
            "Acknowledge progress in each domain",
            "Set positive intentions for coming week"
        ]
    })

    events.append({
        "title": "Dinner + Free Time",
        "time": "7:00-8:30 PM",
        "details": "Nutritious meal and mental break",
        "checkbox_items": [
            "Nutritious meal with enjoyment focus",
            "Complete mental break from technical content",
            "Social or creative activity"
        ]
    })

    events.append({
        "title": "Light Exploration with Wonder Questions",
        "time": "8:30-9:15 PM",
        "details": "Curiosity-driven exploration",
        "checkbox_items": [
            "Select topics for coming week",
            "Create curiosity-driven questions",
            "Brief exploration without pressure",
            "Set learning intentions"
        ]
    })

    events.append({
        "title": "Finance Studies with Weekly Review",
        "time": "9:15-10:00 PM",
        "details": "Financial review and goal setting",
        "checkbox_items": [
            "Review financial learning progress",
            "Update tracking systems",
            "Set specific financial goals for coming week",
            "Create implementation schedule"
        ]
    })

    return events

if __name__ == "__main__":
    # Get today's date
    today = datetime.now(TIMEZONE)  # Fixed this line
    
    # Create events for today in Notion
    created_count = create_events_for_day(today)
    
    # Print database properties (for debugging)
    database = notion.databases.retrieve(DATABASE_ID)
    property_names = list(database["properties"].keys())
    print(f"Available calendar properties: {property_names}")
    
    # Print the events for the current day (for debugging)
    today_events = get_events_for_day(today)
    print(f"Created {created_count} events for {get_current_day()}.")