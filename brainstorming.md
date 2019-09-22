# Questions

- Where is the nearest bus stop (to {location})?
    - req inputs:
        - location
    - optional input:
        - specified location
    - req info:
        - agency_id (while using transloc api)
        - bus stops
    - outputs:
        - bus stop(s)

- When is the next {route} coming (to {location})?
    - req inputs:
        - location
        - route
    - req info:
        - agency_id
        - stops
        - vehicles
    - outputs:
        - time(s) estimate

- Where is the nearest {route} (to {location})?
    - req inputs:
        - location
        - route
    - req info:
        - agency_id
        - vehicles
    - outputs:
        - vehicle location (stop?)
        - time estimate





- Q: How long will it take me to get to {stop}?
- A: "If you catch the bus from the Northline in 10 minutes you can be at Barracks by 1PM"
- Q: When was the last bus?
- A: "The Northline left Runk Dining Hall 10 minutes ago"
- Q: What stops are near me?
- A: "Runk Dining Hall and JMW are near your location"
- Q: Where is the nearest bus stop?
- A: "Runk Dining Hall is 500 feet from your location"
- Q: What's the fastest way to get to {destination}?
- A: "There's an Outer Loop leaving in 2 minutes which will get you there in 10 minutes.
     "There's also an Inner Loop leaving in 5 minutes which will get you there in 15 minutes."
- Q: What's the latest bus I can take to make it to {destination} by {time}?
- A: "Don't miss the Northline coming in 5 minutes"
