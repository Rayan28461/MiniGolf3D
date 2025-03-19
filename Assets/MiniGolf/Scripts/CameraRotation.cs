using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Script which makes camera rotate around ball
/// </summary>
public class CameraRotation : MonoBehaviour
{
    public static CameraRotation instance;

    public float horizontalSpeed = 2f; // used for yaw rotation
    public float stablePitch = 0f;     // fixed pitch angle for x-axis
    public float verticalSpeed = 2f;
    public float minPitch = -45f;
    public float maxPitch = 45f;

    private float currentYaw = 0f;

    private void Awake()
    {
        if (instance == null)
        {
            instance = this;
        }
        else
        {
            Destroy(gameObject);
        }
    }

    /// <summary>
    /// Rotates camera only around y-axis while keeping x-axis stable.
    /// </summary>
    /// <param name="mouseX">Horizontal mouse input</param>
    /// <param name="mouseY">Ignored</param>
    public void RotateCamera(float mouseX, float mouseY)
    {
        currentYaw += mouseX * horizontalSpeed;
        // x-axis remains locked at stablePitch
        transform.localRotation = Quaternion.Euler(stablePitch, currentYaw, 0);
    }
}
