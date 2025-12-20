
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';
import { randomUUID } from 'crypto';

const prisma = new PrismaClient();

async function main() {
  console.log('Seeding database...');

  // Create test admin user
  const hashedPassword = await bcrypt.hash('johndoe123', 10);
  
  const user = await prisma.user.upsert({
    where: { email: 'john@doe.com' },
    update: {},
    create: {
      id: randomUUID(),
      email: 'john@doe.com',
      passwordHash: hashedPassword,
      fullName: 'John Doe',
      companyName: 'Acme Corp',
      jobTitle: 'Compliance Manager',
    },
  });

  console.log('Created user:', user.email);
  console.log('Seeding completed!');
}

main()
  .catch((e) => {
    console.error('Error seeding database:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
