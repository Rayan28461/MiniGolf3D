using System;

namespace MiniGolf.Bus
{
    public static class EventBus<T>
    {
        public static event Action<T> OnEvent;
        public static void Raise(T evt)
        {
            OnEvent?.Invoke(evt);
        }
    }
}
