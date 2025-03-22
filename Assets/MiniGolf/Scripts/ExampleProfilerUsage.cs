using UnityEngine;
using UnityEngine.Profiling;

public class ExampleProfilerUsage : MonoBehaviour
{
    void Update()
    {
        Profiler.BeginSample("Gfx.UploadTexture");
        try
        {
            // ...existing code that uploads texture...
        }
        finally
        {
            Profiler.EndSample();
        }
    }
}
