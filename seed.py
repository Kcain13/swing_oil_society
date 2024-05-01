from app import db
from models import GameType


def add_game_types():
    game_types = [
        {"name": "Match Play", "description": "A game type where players or teams compete on a hole-by-hole basis.",
            "rules": "The player with the lowest number of strokes on an individual hole wins that hole; the player winning the most holes wins the match."},
        {"name": "Stroke Play", "description": "Players compete over a round or series of rounds by counting the total number of strokes taken.",
            "rules": "The total number of strokes taken over one or more rounds determines the winner."},
        {"name": "Tournament Play", "description": "A competitive format typically involving a large number of players participating in an extended event.",
            "rules": "The player with the lowest cumulative score at the end of the tournament is declared the winner."},
        {"name": "Solo Play", "description": "Players play alone focusing on their own scores without direct competition.",
            "rules": "Focuses on personal bests and improving individual performance metrics."}
    ]

    # Get names from the new game types list
    new_type_names = {gt['name'] for gt in game_types}

    # Find and delete any existing game types with the same names
    existing_types = GameType.query.filter(
        GameType.name.in_(new_type_names)).all()
    for et in existing_types:
        db.session.delete(et)
    db.session.commit()

    # Add new game types
    new_game_type_objects = [GameType(**gt) for gt in game_types]
    db.session.bulk_save_objects(new_game_type_objects)
    db.session.commit()


if __name__ == '__main__':
    add_game_types()
    print("Game types have been added to the database.")
