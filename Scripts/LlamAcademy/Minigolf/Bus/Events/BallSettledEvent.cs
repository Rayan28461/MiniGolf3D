using UnityEngine;

namespace LlamAcademy.Minigolf.Bus.Events
{
    public class BallSettledEvent
    {
        public Vector3 Position;
        public BallSettledEvent(Vector3 position)
        {
            Position = position;
        }
    }
}
