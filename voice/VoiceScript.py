import whisper
import sounddevice as sd
import numpy as np
import re
import tempfile
import soundfile as sf
import os
from difflib import SequenceMatcher
import threading
import time

# Load model
model = whisper.load_model("medium")

def calculate_similarity(text1, text2):
    """Calcule la similarité entre deux textes (0-100%)"""
    return int(SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100)

def parse_chef_command(text):
    """Parse chef commands avec comparaison de similarité"""
    text_lower = text.lower().strip()
    print(f"📝 Transcription reçue: '{text}'")
    print(f"🔍 Analyse du texte: '{text_lower}'")
    
    # Extraire les numéros du texte
    numbers = re.findall(r'\d+', text_lower)
    
    if not numbers:
        print("❌ Aucun numéro trouvé dans la transcription")
        # Essayer de reconnaître les numéros en mots
        number_words = {
            'un': '1', 'deux': '2', 'trois': '3', 'quatre': '4', 'cinq': '5',
            'six': '6', 'sept': '7', 'huit': '8', 'neuf': '9', 'dix': '10',
            'onze': '11', 'douze': '12', 'treize': '13', 'quatorze': '14', 'quinze': '15',
            'seize': '16', 'dix-sept': '17', 'dix-huit': '18', 'dix-neuf': '19', 'vingt': '20'
        }
        
        for word, num in number_words.items():
            if word in text_lower:
                numbers = [num]
                print(f"📊 Numéro reconnu en mot: '{word}' → {num}")
                break
    
    if not numbers:
        print("❌ Impossible de détecter un numéro de commande")
        return None
        
    order_number = numbers[0]
    print(f"📊 Numéro de commande: {order_number}")
    
    # Phrases attendues pour comparaison
    expected_lance_phrases = [
        f"commande {order_number} lance",
        f"commande {order_number} lancé",
        f"commande {order_number} lancée"
    ]
    
    expected_prete_phrases = [
        f"commande {order_number} prete",
        f"commande {order_number} prête",
        f"commande {order_number} prêt"
    ]
    
    # Seuil de similarité (70% = assez permissif)
    similarity_threshold = 70
    
    print("\n🔍 Comparaison avec les phrases attendues:")
    
    # Tester similarité avec "lance"
    best_lance_similarity = 0
    best_lance_phrase = ""
    for expected in expected_lance_phrases:
        similarity = calculate_similarity(text_lower, expected)
        print(f"   '{expected}' → {similarity}%")
        if similarity > best_lance_similarity:
            best_lance_similarity = similarity
            best_lance_phrase = expected
    
    # Tester similarité avec "prete"  
    best_prete_similarity = 0
    best_prete_phrase = ""
    for expected in expected_prete_phrases:
        similarity = calculate_similarity(text_lower, expected)
        print(f"   '{expected}' → {similarity}%")
        if similarity > best_prete_similarity:
            best_prete_similarity = similarity
            best_prete_phrase = expected
    
    # Décider quelle commande accepter
    if best_lance_similarity >= similarity_threshold and best_lance_similarity >= best_prete_similarity:
        print(f"✅ ACCEPTÉ comme 'lance': {best_lance_similarity}% de similarité avec '{best_lance_phrase}'")
        return {
            'type': 'lance',
            'order_number': order_number,
            'confidence': best_lance_similarity,
            'matched_phrase': best_lance_phrase,
            'message': f"✅ Commande {order_number} - Préparation lancée! (similarité: {best_lance_similarity}%)"
        }
    elif best_prete_similarity >= similarity_threshold:
        print(f"✅ ACCEPTÉ comme 'prete': {best_prete_similarity}% de similarité avec '{best_prete_phrase}'")
        return {
            'type': 'prete', 
            'order_number': order_number,
            'confidence': best_prete_similarity,
            'matched_phrase': best_prete_phrase,
            'message': f"🍽️ Commande {order_number} - Prête à servir! (similarité: {best_prete_similarity}%)"
        }
    else:
        print(f"❌ REJETÉ: Similarité trop faible")
        print(f"   Meilleure similarité 'lance': {best_lance_similarity}%")
        print(f"   Meilleure similarité 'prete': {best_prete_similarity}%") 
        print(f"   Seuil requis: {similarity_threshold}%")
        return None

def confirm_command(command_info):
    """Demande confirmation vocale pour une commande"""
    print(f"\n🔔 COMMANDE DÉTECTÉE!")
    print(f"📋 {command_info['message']}")
    print(f"🎙️ Voulez-vous confirmer que la commande {command_info['order_number']} est {command_info['type']}?")
    print("💬 Dites 'OUI' pour confirmer ou 'NON' pour annuler...")
    
    # Record confirmation
    try:
        print("🎤 En attente de confirmation...")
        audio = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype='float32')  # 3 seconds
        sd.wait()
        audio = np.squeeze(audio)
        
        # Normalize audio
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.95
        
        # Transcribe confirmation
        result = model.transcribe(audio, language="fr")
        confirmation_text = result["text"].lower().strip()
        print(f"🔍 Réponse entendue: '{confirmation_text}'")
        
        # Check for positive confirmation
        positive_words = ['oui', 'yes', 'ok', 'okay', 'confirme', 'confirmé', 'correct', 'exacte']
        negative_words = ['non', 'no', 'pas', 'annule', 'faux', 'incorrect']
        
        # Calculate similarity for confirmation
        best_positive = max([calculate_similarity(confirmation_text, word) for word in positive_words])
        best_negative = max([calculate_similarity(confirmation_text, word) for word in negative_words])
        
        if best_positive >= 60 and best_positive > best_negative:
            print("✅ CONFIRMÉ! Commande acceptée.")
            return True
        elif best_negative >= 60:
            print("❌ ANNULÉ! Commande rejetée.")
            return False
        else:
            print("❓ Réponse non comprise. Commande annulée par sécurité.")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la confirmation: {e}")
        return False

def continuous_listen_and_transcribe(duration=3, samplerate=16000):
    """Record audio continuously and transcribe"""
    try:
        # Record audio
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()
        audio = np.squeeze(audio)

        # Check if there's actual audio (not just silence)
        if np.max(np.abs(audio)) < 0.01:  # Very quiet audio
            return None

        # Normalize audio
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.95
        
        # Transcribe
        result = model.transcribe(audio, language="fr")
        transcribed_text = result["text"].strip()
        
        # Only return if there's meaningful text
        if len(transcribed_text) > 2:
            return transcribed_text
        return None
                
    except Exception as e:
        print(f"❌ Erreur d'écoute: {e}")
        return None

def chef_voice_interface():
    """Main interface for chef voice commands with continuous listening"""
    print("🍳 Interface vocale pour chef - Écoute continue activée!")
    print("Commandes disponibles:")
    print("  • 'Commande [numéro] lance' - Marquer une commande comme lancée")
    print("  • 'Commande [numéro] prete' - Marquer une commande comme prête")
    print("  • Le système écoute en continu...")
    print("  • Appuyez sur Ctrl+C pour quitter\n")
    
    print("🔄 Écoute continue démarrée...")
    last_command_time = 0  # Pour éviter les répétitions
    
    try:
        while True:
            print("🎧 Écoute...", end="", flush=True)
            
            # Listen continuously in short bursts
            transcribed_text = continuous_listen_and_transcribe(3)
            
            if transcribed_text:
                current_time = time.time()
                print(f"\r📝 Audio détecté: '{transcribed_text}'")
                
                # Parse for chef commands
                command = parse_chef_command(transcribed_text)
                
                if command and (current_time - last_command_time) > 10:  # 10 seconds cooldown
                    # Ask for confirmation
                    if confirm_command(command):
                        # Execute the command
                        if command['type'] == 'lance':
                            print(f"📋 ✅ Commande {command['order_number']} ajoutée à la file de préparation")
                        elif command['type'] == 'prete':
                            print(f"🔔 ✅ Notification envoyée: Commande {command['order_number']} prête")
                        
                        last_command_time = current_time
                        print("\n🔄 Retour à l'écoute continue...")
                    else:
                        print("🔄 Commande annulée. Retour à l'écoute continue...")
                else:
                    # Clear the line and continue listening
                    print("\r", end="", flush=True)
            else:
                # Clear the line and continue
                print("\r", end="", flush=True)
            
            # Small delay to prevent CPU overload
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n👋 Interface vocale arrêtée. Au revoir!")

# Run the chef interface
if __name__ == "__main__":
    chef_voice_interface()
