from .entity import Position, Entity
from math import sqrt


def collision_time(r, obj1, obj2):
    # r: collision_radius
    # With credit to Ben Spector
    # Simplified derivation:
    # 1. Set up the distance between the two entities in terms of time,
       # the difference between their velocities and the difference between
       # their positions
    # 2. Equate the distance equal to the event radius (max possible distance
       # they could be)
    # 3. Solve the resulting quadratic

    dx = obj1.x - obj2.x
    dy = obj1.y - obj2.y
    dvx = obj1.vx - obj2.vx
    dvy = obj1.vy - obj2.vy

    # dx = loc1.x - loc2.x;
    # dy = loc1.y - loc2.y;
    # dvx = vel1.x - vel2.x;
    # dvy = vel1.y - vel2.y;

    # Quadratic formula
    a = dvx**2 + dvy**2
    b = 2 * (dx * dvx + dy * dvy)
    c = dx**2 + dy**2 - r**2

    disc = b**2 - 4 * a * c

    if a == 0.0:
        if b == 0.0:
            if c <= 0.0:
                # Implies r^2 >= dx^2 + dy^2 and the two are already colliding
                return (True, 0.0)
            return (False, 0.0)
        t = -c / b;
        if t >= 0.0:
            return (True, t);
        return (False, 0.0);

    elif disc == 0.0:
        # One solution
        t = -b / (2 * a);
        return (True, t)

    elif disc > 0:
        t1 = -b + sqrt(disc);
        t2 = -b - sqrt(disc);

        if t1 >= 0.0 and t2 >= 0.0:
            return (True, min(t1, t2) / (2 * a))
        elif t1 <= 0.0 and t2 <= 0.0:
            return (True, max(t1, t2) / (2 * a))
        else:
            return (True, 0.0)
    else:
        return (False, 0.0)


def intersect_segment_circle(start, end, circle, *, fudge=0.5):
    """
    Test whether a line segment and circle intersect.

    :param Entity start: The start of the line segment. (Needs x, y attributes)
    :param Entity end: The end of the line segment. (Needs x, y attributes)
    :param Entity circle: The circle to test against. (Needs x, y, r attributes)
    :param float fudge: A fudge factor; additional distance to leave between the segment and circle. (Probably set this to the ship radius, 0.5.)
    :return: True if intersects, False otherwise
    :rtype: bool
    """
    # Derived with SymPy
    # Parameterize the segment as start + t * (end - start),
    # and substitute into the equation of a circle
    # Solve for t
    dx = end.x - start.x
    dy = end.y - start.y

    a = dx**2 + dy**2
    b = -2 * (start.x**2 - start.x*end.x - start.x*circle.x + end.x*circle.x +
              start.y**2 - start.y*end.y - start.y*circle.y + end.y*circle.y)
    c = (start.x - circle.x)**2 + (start.y - circle.y)**2

    if a == 0.0:
        # Start and end are the same point
        return start.calculate_distance_between(circle) <= circle.radius + fudge

    # Time along segment when closest to the circle (vertex of the quadratic)
    t = min(-b / (2 * a), 1.0)
    if t < 0:
        return False

    closest_x = start.x + dx * t
    closest_y = start.y + dy * t
    closest_distance = Position(closest_x, closest_y).calculate_distance_between(circle)

    return closest_distance <= circle.radius + fudge
