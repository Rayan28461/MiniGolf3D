using UnityEngine;

namespace MiniGolf.Events
{
    public interface IEvent { }

    public struct PlayerStrokeEvent : IEvent
    {
        public Vector3 StartPosition;
        public int TotalStrokes;
        
        public PlayerStrokeEvent(Vector3 startPosition, int totalStrokes)
        {
            StartPosition = startPosition;
            TotalStrokes = totalStrokes;
        }
    }

    public struct BallSettledEvent : IEvent
    {
        public Vector3 Position;
        
        public BallSettledEvent(Vector3 position)
        {
            Position = position;
        }
    }
}
