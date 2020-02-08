from django.db import connection, models


class AppointmentTransition(models.Model):
    appointment = models.IntegerField()
    patient = models.IntegerField()
    doctor = models.IntegerField()
    status = models.CharField(max_length=20)
    event = models.CharField(max_length=20, null=True)
    scheduled_time = models.DateTimeField()
    updated_at = models.DateTimeField()

    @staticmethod
    def avg_wait():
        """
        Calculate lifetime average wait time in minutes. -1 if no data exists.
        """
        query = '''
            select avg((strftime('%s', t2.updated_at) - strftime('%s', t1.updated_at)) / 60)
            from drchrono_appointmenttransition t1, drchrono_appointmenttransition t2
            where t1.appointment = t2.appointment and t1.status = 'Arrived' and t2.status = 'In Session';
        '''

        with connection.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()

        if row:
            return row[0]

        return -1
