import json
import random
from datetime import datetime, timedelta
from typing import Dict, List
from models import *

class MockDatabase:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.addresses: Dict[int, Address] = {}
        self.restaurants: Dict[int, Restaurant] = {}
        self.menus: Dict[int, Menu] = {}
        self.menu_categories: Dict[int, MenuCategory] = {}
        self.dishes: Dict[int, Dish] = {}
        self.orders: Dict[int, Order] = {}
        self.order_items: Dict[int, OrderItem] = {}
        self.reviews: Dict[int, Review] = {}
        self.ingredients: Dict[int, Ingredient] = {}
        self.loyalty_cards: Dict[int, LoyaltyCard] = {}
        self.loyalty_transactions: Dict[int, LoyaltyTransaction] = {}
        
        self._populate_data()
    
    def _populate_data(self):
        """Populate the mock database with realistic sample data"""
        
        # Create sample restaurants
        self._create_restaurants()
        
        # Create sample addresses for restaurants
        self._create_restaurant_addresses()
        
        # Create sample menus and categories
        self._create_menus_and_categories()
        
        # Create sample dishes
        self._create_dishes()
        
        # Create sample users with embedded preferences
        self._create_users()
        
        # Create user addresses
        self._create_user_addresses()
        
        # Create sample orders and order items
        self._create_orders()
        
        # Create sample reviews
        self._create_reviews()
        
        # Create loyalty cards and transactions
        self._create_loyalty_system()
        
        # Create ingredients
        self._create_ingredients()
    
    def _create_restaurants(self):
        restaurants_data = [
            {
                "id": 1,
                "name": "La Bella Vista",
                "description": "Authentic Italian cuisine with a modern twist",
                "phone": "+213-555-0101",
                "email": "info@labellavista.dz",
                "website": "https://labellavista.dz",
                "operatingHours": {
                    "monday": {"open": "11:00", "close": "23:00"},
                    "tuesday": {"open": "11:00", "close": "23:00"},
                    "wednesday": {"open": "11:00", "close": "23:00"},
                    "thursday": {"open": "11:00", "close": "23:00"},
                    "friday": {"open": "11:00", "close": "00:00"},
                    "saturday": {"open": "11:00", "close": "00:00"},
                    "sunday": {"open": "12:00", "close": "22:00"}
                },
                "logo": "https://example.com/logo1.jpg",
                "coverImage": "https://example.com/cover1.jpg",
                "gallery": ["https://example.com/gallery1_1.jpg", "https://example.com/gallery1_2.jpg"]
            },
            {
                "id": 2,
                "name": "Spice Palace",
                "description": "Traditional Algerian and Middle Eastern flavors",
                "phone": "+213-555-0102",
                "email": "contact@spicepalace.dz",
                "website": "https://spicepalace.dz",
                "operatingHours": {
                    "monday": {"open": "12:00", "close": "22:00"},
                    "tuesday": {"open": "12:00", "close": "22:00"},
                    "wednesday": {"open": "12:00", "close": "22:00"},
                    "thursday": {"open": "12:00", "close": "22:00"},
                    "friday": {"open": "12:00", "close": "23:00"},
                    "saturday": {"open": "12:00", "close": "23:00"},
                    "sunday": {"open": "13:00", "close": "21:00"}
                },
                "logo": "https://example.com/logo2.jpg",
                "coverImage": "https://example.com/cover2.jpg",
                "gallery": ["https://example.com/gallery2_1.jpg", "https://example.com/gallery2_2.jpg"]
            },
            {
                "id": 3,
                "name": "Ocean Breeze",
                "description": "Fresh seafood and Mediterranean cuisine",
                "phone": "+213-555-0103",
                "email": "hello@oceanbreeze.dz",
                "website": "https://oceanbreeze.dz",
                "operatingHours": {
                    "monday": {"open": "10:00", "close": "22:30"},
                    "tuesday": {"open": "10:00", "close": "22:30"},
                    "wednesday": {"open": "10:00", "close": "22:30"},
                    "thursday": {"open": "10:00", "close": "22:30"},
                    "friday": {"open": "10:00", "close": "23:30"},
                    "saturday": {"open": "10:00", "close": "23:30"},
                    "sunday": {"open": "11:00", "close": "22:00"}
                },
                "logo": "https://example.com/logo3.jpg",
                "coverImage": "https://example.com/cover3.jpg",
                "gallery": ["https://example.com/gallery3_1.jpg", "https://example.com/gallery3_2.jpg"]
            }
        ]
        
        for data in restaurants_data:
            restaurant = Restaurant(**data)
            self.restaurants[restaurant.id] = restaurant
    
    def _create_restaurant_addresses(self):
        addresses_data = [
            {
                "id": 1,
                "restaurantId": 1,
                "street": "123 Rue Didouche Mourad",
                "city": "Algiers",
                "latitude": 36.7538,
                "longitude": 3.0588
            },
            {
                "id": 2,
                "restaurantId": 2,
                "street": "456 Boulevard Colonel Amirouche",
                "city": "Oran",
                "latitude": 35.6969,
                "longitude": -0.6331
            },
            {
                "id": 3,
                "restaurantId": 3,
                "street": "789 Corniche Road",
                "city": "Annaba",
                "latitude": 36.9,
                "longitude": 7.7667
            }
        ]
        
        for data in addresses_data:
            address = Address(**data)
            self.addresses[address.id] = address
    
    def _create_menus_and_categories(self):
        # Create menus
        menus_data = [
            {"id": 1, "restaurantId": 1, "name": "Main Menu", "description": "Our signature dishes"},
            {"id": 2, "restaurantId": 1, "name": "Dessert Menu", "description": "Sweet endings"},
            {"id": 3, "restaurantId": 2, "name": "Traditional Menu", "description": "Authentic local cuisine"},
            {"id": 4, "restaurantId": 2, "name": "Beverages", "description": "Fresh drinks and teas"},
            {"id": 5, "restaurantId": 3, "name": "Seafood Specialties", "description": "Daily fresh catch"},
            {"id": 6, "restaurantId": 3, "name": "Mediterranean", "description": "Mediterranean classics"}
        ]
        
        for data in menus_data:
            menu = Menu(**data)
            self.menus[menu.id] = menu
        
        # Create menu categories
        categories_data = [
            {"id": 1, "menuId": 1, "name": "Appetizers", "description": "Start your meal right"},
            {"id": 2, "menuId": 1, "name": "Pasta", "description": "Homemade pasta dishes"},
            {"id": 3, "menuId": 1, "name": "Pizza", "description": "Wood-fired pizzas"},
            {"id": 4, "menuId": 1, "name": "Main Courses", "description": "Hearty main dishes"},
            {"id": 5, "menuId": 2, "name": "Desserts", "description": "Sweet treats"},
            {"id": 6, "menuId": 3, "name": "Tajines", "description": "Traditional Algerian tajines"},
            {"id": 7, "menuId": 3, "name": "Couscous", "description": "Various couscous dishes"},
            {"id": 8, "menuId": 3, "name": "Grills", "description": "Grilled meats and vegetables"},
            {"id": 9, "menuId": 4, "name": "Hot Beverages", "description": "Teas and coffees"},
            {"id": 10, "menuId": 4, "name": "Cold Beverages", "description": "Refreshing drinks"},
            {"id": 11, "menuId": 5, "name": "Fish", "description": "Fresh fish preparations"},
            {"id": 12, "menuId": 5, "name": "Shellfish", "description": "Prawns, crabs, and more"},
            {"id": 13, "menuId": 6, "name": "Salads", "description": "Fresh Mediterranean salads"},
            {"id": 14, "menuId": 6, "name": "Mezze", "description": "Small plates to share"}
        ]
        
        for data in categories_data:
            category = MenuCategory(**data)
            self.menu_categories[category.id] = category
    
    def _create_dishes(self):
        dishes_data = [
            # La Bella Vista (Italian) - Restaurant 1
            {"id": 1, "categoryId": 1, "name": "Bruschetta al Pomodoro", "description": "Grilled bread with fresh tomatoes, basil, and garlic", "price": 850.0, "preparationTime": 10, "popularity": 8.5},
            {"id": 2, "categoryId": 1, "name": "Antipasto Misto", "description": "Mixed Italian appetizers with cured meats and cheeses", "price": 1200.0, "preparationTime": 15, "popularity": 7.8},
            {"id": 3, "categoryId": 2, "name": "Spaghetti Carbonara", "description": "Classic pasta with eggs, cheese, and pancetta", "price": 1450.0, "preparationTime": 20, "popularity": 9.2},
            {"id": 4, "categoryId": 2, "name": "Penne Arrabbiata", "description": "Penne pasta in spicy tomato sauce", "price": 1250.0, "preparationTime": 18, "popularity": 7.5},
            {"id": 5, "categoryId": 2, "name": "Fettuccine Alfredo", "description": "Creamy pasta with parmesan cheese", "price": 1350.0, "preparationTime": 15, "popularity": 8.1},
            {"id": 6, "categoryId": 3, "name": "Margherita Pizza", "description": "Classic pizza with tomato, mozzarella, and basil", "price": 1100.0, "preparationTime": 25, "popularity": 9.5},
            {"id": 7, "categoryId": 3, "name": "Quattro Stagioni", "description": "Four seasons pizza with various toppings", "price": 1550.0, "preparationTime": 30, "popularity": 8.7},
            {"id": 8, "categoryId": 4, "name": "Osso Buco", "description": "Braised veal shanks with vegetables", "price": 2800.0, "preparationTime": 45, "popularity": 8.9},
            {"id": 9, "categoryId": 4, "name": "Chicken Parmigiana", "description": "Breaded chicken with marinara and cheese", "price": 1950.0, "preparationTime": 35, "popularity": 8.3},
            {"id": 10, "categoryId": 5, "name": "Tiramisu", "description": "Classic Italian dessert with coffee and mascarpone", "price": 650.0, "preparationTime": 5, "popularity": 9.1},
            {"id": 11, "categoryId": 5, "name": "Panna Cotta", "description": "Silky smooth vanilla dessert", "price": 550.0, "preparationTime": 5, "popularity": 7.9},
            
            # Spice Palace (Algerian/Middle Eastern) - Restaurant 2
            {"id": 12, "categoryId": 6, "name": "Chicken Tajine", "description": "Slow-cooked chicken with vegetables and spices", "price": 1650.0, "preparationTime": 40, "popularity": 9.0},
            {"id": 13, "categoryId": 6, "name": "Lamb Tajine", "description": "Tender lamb with dried fruits and almonds", "price": 2200.0, "preparationTime": 50, "popularity": 8.8},
            {"id": 14, "categoryId": 6, "name": "Vegetable Tajine", "description": "Seasonal vegetables in aromatic spices", "price": 1200.0, "preparationTime": 35, "popularity": 7.6},
            {"id": 15, "categoryId": 7, "name": "Couscous Royal", "description": "Traditional couscous with meat and vegetables", "price": 1800.0, "preparationTime": 45, "popularity": 9.3},
            {"id": 16, "categoryId": 7, "name": "Fish Couscous", "description": "Couscous with fresh fish and vegetables", "price": 1950.0, "preparationTime": 40, "popularity": 8.4},
            {"id": 17, "categoryId": 8, "name": "Mixed Grill", "description": "Assorted grilled meats with sides", "price": 2500.0, "preparationTime": 30, "popularity": 8.6},
            {"id": 18, "categoryId": 8, "name": "Grilled Lamb Chops", "description": "Marinated lamb chops with herbs", "price": 2800.0, "preparationTime": 25, "popularity": 9.1},
            {"id": 19, "categoryId": 9, "name": "Mint Tea", "description": "Traditional Algerian mint tea", "price": 250.0, "preparationTime": 5, "popularity": 9.4},
            {"id": 20, "categoryId": 9, "name": "Turkish Coffee", "description": "Strong traditional coffee", "price": 300.0, "preparationTime": 8, "popularity": 8.2},
            {"id": 21, "categoryId": 10, "name": "Fresh Orange Juice", "description": "Freshly squeezed orange juice", "price": 400.0, "preparationTime": 3, "popularity": 8.7},
            
            # Ocean Breeze (Seafood/Mediterranean) - Restaurant 3
            {"id": 22, "categoryId": 11, "name": "Grilled Sea Bass", "description": "Fresh sea bass with lemon and herbs", "price": 2400.0, "preparationTime": 25, "popularity": 9.2},
            {"id": 23, "categoryId": 11, "name": "Salmon Teriyaki", "description": "Glazed salmon with Asian flavors", "price": 2650.0, "preparationTime": 20, "popularity": 8.8},
            {"id": 24, "categoryId": 11, "name": "Fish and Chips", "description": "Beer-battered fish with fries", "price": 1650.0, "preparationTime": 18, "popularity": 8.1},
            {"id": 25, "categoryId": 12, "name": "Seafood Paella", "description": "Spanish rice dish with mixed seafood", "price": 2800.0, "preparationTime": 35, "popularity": 9.0},
            {"id": 26, "categoryId": 12, "name": "Grilled Prawns", "description": "Large prawns with garlic butter", "price": 2200.0, "preparationTime": 15, "popularity": 8.7},
            {"id": 27, "categoryId": 13, "name": "Greek Salad", "description": "Fresh vegetables with feta and olives", "price": 950.0, "preparationTime": 10, "popularity": 8.4},
            {"id": 28, "categoryId": 13, "name": "Caesar Salad", "description": "Romaine lettuce with Caesar dressing", "price": 850.0, "preparationTime": 10, "popularity": 7.9},
            {"id": 29, "categoryId": 14, "name": "Hummus Platter", "description": "Homemade hummus with vegetables and bread", "price": 750.0, "preparationTime": 8, "popularity": 8.3},
            {"id": 30, "categoryId": 14, "name": "Mixed Mezze", "description": "Assortment of Mediterranean small plates", "price": 1450.0, "preparationTime": 12, "popularity": 8.9}
        ]
        
        for data in dishes_data:
            dish = Dish(**data)
            self.dishes[dish.id] = dish
    
    def _create_users(self):
        # Sample embedded preferences for different user types
        user_preferences = [
            # User 1 - Italian food lover, vegetarian-friendly
            {
                "cuisine_preferences": ["Italian", "Mediterranean"],
                "dietary_restrictions": ["vegetarian_friendly"],
                "price_range": {"min": 800, "max": 2000},
                "favorite_flavors": ["garlic", "basil", "tomato", "cheese"],
                "spice_level": "mild",
                "meal_times": ["lunch", "dinner"],
                "cooking_methods": ["grilled", "baked"],
                "allergens_to_avoid": []
            },
            # User 2 - Adventurous eater, loves spicy food
            {
                "cuisine_preferences": ["Middle Eastern", "North African", "Spicy"],
                "dietary_restrictions": [],
                "price_range": {"min": 1000, "max": 3000},
                "favorite_flavors": ["spicy", "lamb", "chicken", "mint"],
                "spice_level": "hot",
                "meal_times": ["lunch", "dinner"],
                "cooking_methods": ["grilled", "slow_cooked"],
                "allergens_to_avoid": []
            },
            # User 3 - Seafood enthusiast
            {
                "cuisine_preferences": ["Seafood", "Mediterranean", "Light"],
                "dietary_restrictions": ["pescatarian"],
                "price_range": {"min": 1200, "max": 3000},
                "favorite_flavors": ["fish", "lemon", "herbs", "olive_oil"],
                "spice_level": "mild",
                "meal_times": ["lunch", "dinner"],
                "cooking_methods": ["grilled", "steamed"],
                "allergens_to_avoid": ["shellfish"]
            },
            # User 4 - Budget-conscious, simple tastes
            {
                "cuisine_preferences": ["Simple", "Comfort Food"],
                "dietary_restrictions": [],
                "price_range": {"min": 500, "max": 1500},
                "favorite_flavors": ["chicken", "pasta", "bread"],
                "spice_level": "mild",
                "meal_times": ["lunch", "dinner"],
                "cooking_methods": ["fried", "baked"],
                "allergens_to_avoid": []
            },
            # User 5 - Health-conscious, salad lover
            {
                "cuisine_preferences": ["Healthy", "Mediterranean", "Fresh"],
                "dietary_restrictions": ["low_calorie", "gluten_conscious"],
                "price_range": {"min": 600, "max": 1800},
                "favorite_flavors": ["vegetables", "olive_oil", "lemon", "herbs"],
                "spice_level": "mild",
                "meal_times": ["lunch", "light_dinner"],
                "cooking_methods": ["raw", "grilled", "steamed"],
                "allergens_to_avoid": ["gluten"]
            }
        ]
        
        users_data = [
            {
                "id": 1,
                "email": "ahmed.belkacem@email.com",
                "phone": 213555001,
                "firstName": "Ahmed",
                "lastName": "Belkacem",
                "role": UserRole.CLIENT,
                "password": "hashed_password_1",
                "embeddedPref": json.dumps(user_preferences[0]),
                "specialinfo": {"age": 28, "occupation": "Engineer", "dining_frequency": "weekly"}
            },
            {
                "id": 2,
                "email": "fatima.bensaid@email.com",
                "phone": 213555002,
                "firstName": "Fatima",
                "lastName": "Bensaid",
                "password": "hashed_password_2",
                "embeddedPref": json.dumps(user_preferences[1]),
                "specialinfo": {"age": 35, "occupation": "Teacher", "dining_frequency": "bi-weekly"}
            },
            {
                "id": 3,
                "email": "karim.meziane@email.com",
                "phone": 213555003,
                "firstName": "Karim",
                "lastName": "Meziane",
                "password": "hashed_password_3",
                "embeddedPref": json.dumps(user_preferences[2]),
                "specialinfo": {"age": 42, "occupation": "Doctor", "dining_frequency": "weekly"}
            },
            {
                "id": 4,
                "email": "sara.hamidi@email.com",
                "phone": 213555004,
                "firstName": "Sara",
                "lastName": "Hamidi",
                "password": "hashed_password_4",
                "embeddedPref": json.dumps(user_preferences[3]),
                "specialinfo": {"age": 24, "occupation": "Student", "dining_frequency": "monthly"}
            },
            {
                "id": 5,
                "email": "omar.benali@email.com",
                "phone": 213555005,
                "firstName": "Omar",
                "lastName": "Benali",
                "password": "hashed_password_5",
                "embeddedPref": json.dumps(user_preferences[4]),
                "specialinfo": {"age": 31, "occupation": "Nutritionist", "dining_frequency": "weekly"}
            }
        ]
        
        for data in users_data:
            user = User(**data)
            self.users[user.id] = user
    
    def _create_user_addresses(self):
        addresses_data = [
            {"id": 4, "userId": 1, "street": "15 Rue Ben M'Hidi", "city": "Algiers", "latitude": 36.7755, "longitude": 3.0597, "isDefault": True},
            {"id": 5, "userId": 2, "street": "27 Boulevard Zabana", "city": "Oran", "latitude": 35.6911, "longitude": -0.6417, "isDefault": True},
            {"id": 6, "userId": 3, "street": "8 Avenue de l'ALN", "city": "Annaba", "latitude": 36.9147, "longitude": 7.7622, "isDefault": True},
            {"id": 7, "userId": 4, "street": "42 Rue Larbi Ben M'Hidi", "city": "Algiers", "latitude": 36.7831, "longitude": 3.0668, "isDefault": True},
            {"id": 8, "userId": 5, "street": "33 Place du 1er Novembre", "city": "Oran", "latitude": 35.6969, "longitude": -0.6331, "isDefault": True}
        ]
        
        for data in addresses_data:
            address = Address(**data)
            self.addresses[address.id] = address
    
    def _create_orders(self):
        # Create realistic orders with order items
        order_counter = 1
        item_counter = 1
        
        # Sample orders for each user
        for user_id in self.users.keys():
            # Create 3-5 orders per user with varying dates
            for order_num in range(random.randint(3, 5)):
                order = Order(
                    id=order_counter,
                    orderNumber=f"ORD{order_counter:06d}",
                    userId=user_id,
                    restaurantId=random.choice(list(self.restaurants.keys())),
                    type=random.choice(list(OrderType)),
                    status=random.choice([OrderStatus.COMPLETED, OrderStatus.COMPLETED, OrderStatus.COMPLETED, OrderStatus.PENDING]),
                    paymentStatus=PaymentStatus.PAID if random.random() > 0.1 else PaymentStatus.PENDING
                )
                
                # Add 1-4 items to each order
                order_total = 0
                num_items = random.randint(1, 4)
                
                for _ in range(num_items):
                    # Select dishes from the restaurant
                    available_dishes = [d for d in self.dishes.values() 
                                     if any(mc.menuId in [m.id for m in self.menus.values() 
                                           if m.restaurantId == order.restaurantId] 
                                           for mc in self.menu_categories.values() 
                                           if mc.id == d.categoryId)]
                    
                    if available_dishes:
                        dish = random.choice(available_dishes)
                        quantity = random.randint(1, 3)
                        unit_price = dish.price
                        total_price = unit_price * quantity
                        
                        order_item = OrderItem(
                            id=item_counter,
                            orderId=order.id,
                            dishId=dish.id,
                            quantity=quantity,
                            unitPrice=unit_price,
                            totalPrice=total_price
                        )
                        
                        self.order_items[item_counter] = order_item
                        item_counter += 1
                        order_total += total_price
                
                order.subtotal = order_total
                order.totalAmount = order_total + order.deliveryFee - order.discount
                
                self.orders[order_counter] = order
                order_counter += 1
    
    def _create_reviews(self):
        review_counter = 1
        
        # Create reviews for completed orders
        for order in self.orders.values():
            if order.status == OrderStatus.COMPLETED and random.random() > 0.3:  # 70% chance of review
                # Get dishes from this order
                order_dishes = [oi.dishId for oi in self.order_items.values() if oi.orderId == order.id]
                
                # Restaurant review
                restaurant_rating = random.randint(3, 5)
                restaurant_comments = [
                    "Great experience overall!",
                    "Food was delicious and service was excellent.",
                    "Will definitely come back again.",
                    "Good quality food at reasonable prices.",
                    "Nice atmosphere and friendly staff.",
                    "Fast service and tasty food.",
                    "Authentic flavors and fresh ingredients."
                ]
                
                restaurant_review = Review(
                    id=review_counter,
                    userId=order.userId,
                    restaurantId=order.restaurantId,
                    rating=restaurant_rating,
                    comment=random.choice(restaurant_comments),
                    sentiment="positive" if restaurant_rating >= 4 else "neutral",
                    sentimentScore=0.8 if restaurant_rating >= 4 else 0.5,
                    isVerified=True
                )
                
                self.reviews[review_counter] = restaurant_review
                review_counter += 1
                
                # Dish reviews (sometimes)
                for dish_id in order_dishes:
                    if random.random() > 0.7:  # 30% chance of dish review
                        dish_rating = random.randint(3, 5)
                        dish_comments = [
                            "Perfectly cooked and seasoned!",
                            "Loved the flavors in this dish.",
                            "Great portion size and taste.",
                            "Would order this again.",
                            "Fresh ingredients and good preparation.",
                            "Exceeded my expectations!",
                            "Authentic and delicious."
                        ]
                        
                        dish_review = Review(
                            id=review_counter,
                            userId=order.userId,
                            restaurantId=order.restaurantId,
                            dishId=dish_id,
                            rating=dish_rating,
                            comment=random.choice(dish_comments),
                            sentiment="positive" if dish_rating >= 4 else "neutral",
                            sentimentScore=0.85 if dish_rating >= 4 else 0.5,
                            isVerified=True
                        )
                        
                        self.reviews[review_counter] = dish_review
                        review_counter += 1
    
    def _create_loyalty_system(self):
        # Create loyalty cards for active users
        for user_id in self.users.keys():
            points = random.randint(50, 500)
            loyalty_card = LoyaltyCard(
                id=user_id,
                userId=user_id,
                points=points
            )
            self.loyalty_cards[user_id] = loyalty_card
            
            # Create some loyalty transactions
            transaction_counter = user_id * 10
            for _ in range(random.randint(2, 6)):
                restaurant_id = random.choice(list(self.restaurants.keys()))
                transaction_points = random.randint(10, 50)
                transaction_type = random.choice(["EARNED", "REDEEMED"])
                
                if transaction_type == "REDEEMED":
                    transaction_points = -transaction_points
                
                transaction = LoyaltyTransaction(
                    id=transaction_counter,
                    loyaltyCardId=loyalty_card.id,
                    restaurantId=restaurant_id,
                    points=transaction_points,
                    type=transaction_type,
                    description=f"Points {transaction_type.lower()} from order"
                )
                
                self.loyalty_transactions[transaction_counter] = transaction
                transaction_counter += 1
    
    def _create_ingredients(self):
        ingredient_counter = 1
        sample_ingredients = [
            "tomatoes", "mozzarella", "basil", "olive_oil", "garlic", "onions",
            "chicken", "lamb", "beef", "fish", "prawns", "eggs", "flour",
            "pasta", "rice", "vegetables", "herbs", "spices", "lemon", "butter"
        ]
        
        # Add ingredients to dishes
        for dish_id in self.dishes.keys():
            # Each dish gets 3-6 ingredients
            num_ingredients = random.randint(3, 6)
            dish_ingredients = random.sample(sample_ingredients, num_ingredients)
            
            for ingredient_name in dish_ingredients:
                ingredient = Ingredient(
                    id=ingredient_counter,
                    dishId=dish_id,
                    quantity=round(random.uniform(0.1, 2.0), 1)
                )
                self.ingredients[ingredient_counter] = ingredient
                ingredient_counter += 1

# Create global instance
mock_db = MockDatabase()